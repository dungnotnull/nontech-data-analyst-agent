from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
import uuid
import shutil
from pathlib import Path

from src.config.settings import settings, UPLOAD_DIR
from src.data.file_loader import FileLoader
from src.data.schema_detector import SchemaDetector
from src.data.cleaner import DataCleaner
from src.api.logging_config import get_logger

logger = get_logger("routes.upload")
router = APIRouter()
session_store: dict[str, dict] = {}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Vui lòng chọn một file.")

    ext = Path(file.filename).suffix.lower()
    if ext not in (".xlsx", ".xls", ".csv", ".tsv"):
        raise HTTPException(
            status_code=400,
            detail=f"Định dạng không hỗ trợ: {ext}. Hỗ trợ: .xlsx, .xls, .csv, .tsv",
        )

    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File quá lớn: {file_size_mb:.1f}MB. Tối đa: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    session_id = str(uuid.uuid4())
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    file_path = session_dir / f"data{ext}"
    with open(file_path, "wb") as f:
        f.write(content)

    logger.info("File saved", extra={"session_id": session_id, "file": file.filename, "size_mb": round(file_size_mb, 2)})

    try:
        loader = FileLoader()
        dfs = loader.load(str(file_path))

        cleaner = DataCleaner()
        detector = SchemaDetector()
        schemas = {}
        for sheet_name, df in dfs.items():
            df_clean = cleaner.clean(df)
            dfs[sheet_name] = df_clean
            schemas[sheet_name] = detector.detect(df_clean)

        session_store[session_id] = {
            "file_path": str(file_path),
            "schemas": schemas,
            "session_dir": str(session_dir),
            "created_at": uuid.uuid1().time,
        }

        logger.info("File processed", extra={
            "session_id": session_id,
            "sheets": list(dfs.keys()),
            "rows": sum(len(d) for d in dfs.values()),
        })

        return JSONResponse({
            "session_id": session_id,
            "file_name": file.filename,
            "file_size_mb": round(file_size_mb, 2),
            "sheets": list(dfs.keys()),
            "schemas": schemas,
        })

    except Exception as e:
        shutil.rmtree(session_dir, ignore_errors=True)
        logger.exception("Upload processing failed", extra={"session_id": session_id})
        raise HTTPException(status_code=422, detail=f"Không thể đọc file: {str(e)}")
