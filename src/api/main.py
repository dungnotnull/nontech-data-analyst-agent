from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from src.api.routes import upload, analyze, knowledge
from src.api.rate_limiter import upload_limiter, analyze_limiter
from src.api.logging_config import get_logger
from src.api.session_cleaner import SessionCleaner
from src.config.settings import settings

logger = get_logger("api")
session_cleaner = SessionCleaner()


@asynccontextmanager
async def lifespan(application: FastAPI):
    session_cleaner.start_periodic(interval_minutes=60)
    logger.info("NonTech Data Analyst Agent started", extra={"env": settings.APP_ENV})
    yield
    session_cleaner.stop()
    logger.info("Server shutting down")


app = FastAPI(
    title="NonTech Data Analyst Agent",
    description="AI business analyst for non-technical users — no SQL, no Python, no headaches.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.APP_DEBUG else None,
    redoc_url="/redoc" if settings.APP_DEBUG else None,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    elapsed_ms = (time.time() - start_time) * 1000

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.1f}"
    response.headers["Server"] = ""

    if elapsed_ms > 5000:
        logger.warning(
            "Slow request", extra={
                "path": request.url.path,
                "method": request.method,
                "elapsed_ms": elapsed_ms,
            }
        )

    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path

    if path.startswith("/api/upload"):
        if not upload_limiter.is_allowed(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Quá nhiều file tải lên. Vui lòng thử lại sau 1 giờ."},
            )
    elif path.startswith("/api/analyze"):
        if not analyze_limiter.is_allowed(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Quá nhiều yêu cầu. Vui lòng thử lại sau 1 giờ."},
            )

    response = await call_next(request)
    return response


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    logger.info(
        "Request started",
        extra={"method": request.method, "path": request.url.path, "client": request.client.host if request.client else "unknown"},
    )
    try:
        response = await call_next(request)
        logger.info(
            "Request completed",
            extra={"method": request.method, "path": request.url.path, "status": response.status_code},
        )
        return response
    except Exception as e:
        logger.exception("Request failed", extra={"method": request.method, "path": request.url.path})
        return JSONResponse(
            status_code=500,
            content={"detail": "Đã xảy ra lỗi. Vui lòng thử lại sau."},
        )


app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(analyze.router, prefix="/api", tags=["analyze"])
app.include_router(knowledge.router, prefix="/api", tags=["knowledge"])


@app.get("/health")
async def health_check():
    return JSONResponse({
        "status": "ok",
        "version": "0.1.0",
        "timestamp": time.time(),
    })


@app.get("/")
async def root():
    return {
        "message": "NonTech Data Analyst Agent API",
        "docs": "/docs",
        "health": "/health",
    }
