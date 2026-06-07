from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.agent.knowledge_updater import KnowledgeUpdater, get_knowledge_updater
from src.api.logging_config import get_logger
from src.config.settings import settings

logger = get_logger("routes.knowledge")
router = APIRouter()


@router.get("/knowledge/status")
async def knowledge_status():
    updater = get_knowledge_updater()
    status = updater.get_status()
    return JSONResponse(status)


@router.post("/knowledge/update")
async def trigger_knowledge_update():
    logger.info("Manual knowledge update triggered")
    updater = get_knowledge_updater()
    result = updater.run_update()
    logger.info("Knowledge update completed", extra={"papers_added": result.get("papers_added", 0)})
    return JSONResponse(result)


@router.get("/knowledge/search")
async def search_knowledge(q: str = "", top_k: int = 3):
    if not q.strip():
        return JSONResponse({"results": []})
    updater = get_knowledge_updater()
    results = updater.search(q, top_k=top_k)
    return JSONResponse({"query": q, "results": results})
