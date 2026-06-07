import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.config.settings import settings, LOG_DIR


def setup_logging(app_name: str = "nontech-analyst") -> logging.Logger:
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.APP_DEBUG else logging.INFO)
    console_handler.setFormatter(formatter)
    try:
        console_handler.stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    logger.addHandler(console_handler)

    log_file = LOG_DIR / "app.log"
    try:
        file_handler = RotatingFileHandler(
            str(log_file),
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        pass

    error_log_file = LOG_DIR / "error.log"
    try:
        error_handler = RotatingFileHandler(
            str(error_log_file),
            maxBytes=10 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
    except Exception:
        pass

    return logger


logger = setup_logging()


def get_logger(name: str) -> logging.Logger:
    child = logger.getChild(name)
    return child
