from src.config.settings import settings


LLM_REGISTRY = {
    "claude": {
        "default_model": "claude-sonnet-4-20250514",
        "env_key": "ANTHROPIC_API_KEY",
        "fallback_key": "LLM_API_KEY",
    },
    "openai": {
        "default_model": "gpt-4o",
        "env_key": "OPENAI_API_KEY",
        "fallback_key": "LLM_API_KEY",
    },
    "gemini": {
        "default_model": "gemini-1.5-pro",
        "env_key": "GEMINI_API_KEY",
        "fallback_key": "LLM_API_KEY",
    },
    "local": {
        "default_model": "microsoft/phi-3-mini-4k-instruct",
        "env_key": None,
        "fallback_key": None,
    },
}

FALLBACK_CHAIN = [
    "claude",
    "openai",
    "gemini",
    "local",
]


def get_llm_config() -> dict:
    provider = settings.LLM_PROVIDER
    if provider not in LLM_REGISTRY:
        provider = "local"

    cfg = LLM_REGISTRY[provider]
    api_key = None

    if cfg["env_key"]:
        import os
        api_key = os.getenv(cfg["env_key"]) or os.getenv(cfg["fallback_key"], "")

    model = settings.LLM_MODEL or cfg["default_model"]

    return {
        "provider": provider,
        "model": model,
        "api_key": api_key,
    }


def sanitize_for_llm(df, max_rows: int = 20):
    """Return schema + sample rows for safe LLM transmission."""
    schema = {
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "row_count": len(df),
    }
    samples = df.head(max_rows).to_dict(orient="records")
    summary = df.describe(include="all").to_dict()
    return {
        "schema": schema,
        "samples": samples,
        "summary": summary,
    }
