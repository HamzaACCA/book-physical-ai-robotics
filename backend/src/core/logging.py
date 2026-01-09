"""Logging configuration for the application."""

import logging
import sys
from typing import Any, Dict

from backend.src.core.config import settings


def setup_logging() -> None:
    """Configure application logging with structured output."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name."""
    return logging.getLogger(name)


def log_query_metrics(
    query_id: str,
    retrieval_quality: float,
    latency_ms: int,
    validation_passed: bool,
    extra: Dict[str, Any] | None = None,
) -> None:
    """Log query processing metrics for monitoring."""
    logger = get_logger("query_metrics")
    metrics = {
        "query_id": query_id,
        "retrieval_quality": retrieval_quality,
        "latency_ms": latency_ms,
        "validation_passed": validation_passed,
    }
    if extra:
        metrics.update(extra)

    logger.info(f"Query metrics: {metrics}")
