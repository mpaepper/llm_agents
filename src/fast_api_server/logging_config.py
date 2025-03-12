import logging
import logging.config
import sys
from typing import Any, Dict

from .config import get_settings


def setup_logging() -> None:
    """Configure logging for the application."""
    settings = get_settings()
    
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "default",
                "level": settings.log_level,
            },
        },
        "root": {"handlers": ["console"], "level": settings.log_level},
        "loggers": {
            "fast_api_server": {
                "handlers": ["console"],
                "level": settings.log_level,
                "propagate": False,
            },
            "uvicorn": {"handlers": ["console"], "level": settings.log_level},
            "fastapi": {"handlers": ["console"], "level": settings.log_level},
        },
    }
    
    logging.config.dictConfig(logging_config)
    
    # Create a logger for this module
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully") 