from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pathlib import Path
from typing import Any
import pandas as pd
import numpy as np

from src.agent.intent_parser import IntentParser
from src.agent.code_generator import CodeGenerator
from src.agent.chart_renderer import ChartRenderer
from src.agent.narrative_writer import NarrativeWriter
from src.api.sandbox import PythonSandbox, execute_with_retry
from src.api.logging_config import get_logger
from src.data.file_loader import FileLoader
from src.config.settings import settings

from src.api.routes.upload import session_store

logger = get_logger("routes.analyze")
router = APIRouter()


def _serialize_result(result: Any) -> Any:
    if isinstance(result, pd.DataFrame):
        return result.to_dict(orient="records")
    if isinstance(result, pd.Series):
        return result.to_dict()
    if isinstance(result, np.ndarray):
        return result.tolist()
    if isinstance(result, (np.integer,)):
        return int(result)
    if isinstance(result, (np.floating,)):
        return float(result)
    if isinstance(result, dict):
        return {k: _serialize_result(v) for k, v in result.items()}
    if isinstance(result, list):
        return [_serialize_result(v) for v in result]
    return result


class AnalyzeRequest(BaseModel):
    session_id: str
    question: str


class AnalyzeResponse(BaseModel):
    session_id: str
    question: str
    intent: dict
    result: Any = None
    chart_html: str | None = None
    narrative: str = ""
    recommendation: str | None = None
    error: str | None = None

    model_config = {"arbitrary_types_allowed": True}


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_data(request: AnalyzeRequest):
    session = session_store.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Phiên làm việc không tồn tại. Vui lòng tải file lên trước.")

    logger.info("Analysis requested", extra={
        "session_id": request.session_id,
        "question": request.question[:100],
    })

    try:
        loader = FileLoader()
        dfs = loader.load(session["file_path"])

        parser = IntentParser()
        first_df = list(dfs.values())[0] if dfs else None
        intent = parser.parse_with_schema(request.question, first_df) if first_df is not None else parser.parse(request.question)

        logger.info("Intent parsed", extra={
            "analysis_type": intent.get("analysis_type"),
            "metric": intent.get("metric"),
        })

        sandbox = PythonSandbox(Path(session["session_dir"]))

        generator = CodeGenerator()
        sandbox_result = execute_with_retry(
            sandbox,
            generator.generate,
            intent,
            dfs,
            max_retries=3,
        )

        if not sandbox_result.get("success"):
            logger.warning("Sandbox execution failed", extra={
                "error": sandbox_result.get("error"),
            })
            return AnalyzeResponse(
                session_id=request.session_id,
                question=request.question,
                intent=intent,
                result=None,
                chart_html=None,
                narrative="",
                recommendation=None,
                error=sandbox_result.get("error", "Không thể thực thi phân tích."),
            )

        chart_html = None
        try:
            renderer = ChartRenderer()
            chart_html = renderer.render(intent, sandbox_result.get("result"))
        except Exception as e:
            logger.warning("Chart rendering failed", extra={"error": str(e)})

        writer = NarrativeWriter()
        narrative, recommendation = writer.write(
            intent=intent,
            result=sandbox_result.get("result"),
        )

        logger.info("Analysis complete", extra={
            "session_id": request.session_id,
            "analysis_type": intent.get("analysis_type"),
            "has_chart": chart_html is not None,
            "has_recommendation": recommendation is not None,
        })

        serializable = _serialize_result(sandbox_result.get("result"))

        return AnalyzeResponse(
            session_id=request.session_id,
            question=request.question,
            intent=intent,
            result=serializable,
            chart_html=chart_html,
            narrative=narrative,
            recommendation=recommendation,
            error=None,
        )

    except Exception as e:
        logger.exception("Analysis failed", extra={"session_id": request.session_id})
        return AnalyzeResponse(
            session_id=request.session_id,
            question=request.question,
            intent={},
            result=None,
            chart_html=None,
            narrative="",
            recommendation=None,
            error=str(e),
        )


@router.get("/analyze/history/{session_id}")
async def get_analysis_history(session_id: str):
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Phiên làm việc không tồn tại.")
    return JSONResponse({"session_id": session_id, "history": session.get("history", [])})
