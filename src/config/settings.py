import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
LOG_DIR = DATA_DIR / "logs"
CHROMA_DIR = DATA_DIR / "chroma"

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)


class Settings:
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_DEBUG: bool = os.getenv("APP_DEBUG", "true").lower() == "true"
    APP_SECRET_KEY: str = os.getenv("APP_SECRET_KEY", "dev-secret")

    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
    SESSION_TTL_HOURS: int = int(os.getenv("SESSION_TTL_HOURS", "24"))

    SANDBOX_TIMEOUT_SECONDS: int = int(os.getenv("SANDBOX_TIMEOUT_SECONDS", "30"))
    SANDBOX_MAX_MEMORY_MB: int = int(os.getenv("SANDBOX_MAX_MEMORY_MB", "512"))

    KNOWLEDGE_CRAWL_ENABLED: bool = os.getenv("KNOWLEDGE_CRAWL_ENABLED", "false").lower() == "true"
    KNOWLEDGE_CRAWL_SCHEDULE: str = os.getenv("KNOWLEDGE_CRAWL_SCHEDULE", "0 2 * * 1")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "claude")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "claude-sonnet-4-20250514")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    CRAWL_SOURCES: dict = {
        "arxiv": {
            "topics": [
                "time series forecasting retail",
                "natural language to pandas",
                "business data analysis LLM",
                "Vietnamese NLP",
                "anomaly detection tabular data",
                "customer segmentation deep learning",
            ],
            "max_papers_per_topic": 5,
            "sort_by": "submittedDate",
        },
        "semantic_scholar": {
            "topics": [
                "retail analytics machine learning",
                "small business data analysis",
                "demand forecasting deep learning",
            ],
            "max_papers_per_topic": 5,
        },
        "documentation": [
            "https://facebook.github.io/prophet/docs/",
            "https://nixtlaverse.nixtla.io/statsforecast/",
            "https://scikit-learn.org/stable/modules/outlier_detection.html",
            "https://docs.anthropic.com/en/docs/",
            "https://huggingface.co/vinai/phobert-base-v2",
        ],
    }


settings = Settings()
