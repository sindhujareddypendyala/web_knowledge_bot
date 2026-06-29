"""
Logging utilities for the Website Knowledge Module.

Purpose:
    Provides one consistent logging setup for FastAPI routes, crawlers,
    retrievers, ChromaDB operations, website management, and integrations.

How it connects:
    Every module imports `get_logger(__name__)`. Long-running crawl jobs can
    additionally call `get_crawl_logger(website_id)` to write per-website crawl
    traces that are easy to inspect from API responses or support tickets.
"""

from __future__ import annotations

import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from config import LOGS_PATH, settings

LOG_DIR = Path(LOGS_PATH)
LOG_DIR.mkdir(parents=True, exist_ok=True)

APP_LOG_FILE = LOG_DIR / "app.log"
CRAWL_LOG_DIR = LOG_DIR / "crawls"
CRAWL_LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_LOG_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5

_CONFIGURED_LOGGERS: set[str] = set()


class JsonContextFormatter(logging.Formatter):
    """Formatter that appends JSON context when a record carries `context`."""

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        context = getattr(record, "context", None)
        if not context:
            return message

        try:
            encoded_context = json.dumps(context, ensure_ascii=False, default=str)
        except TypeError:
            encoded_context = json.dumps(str(context), ensure_ascii=False)
        return f"{message} | context={encoded_context}"


def _resolve_level(level: int | str | None = None) -> int:
    if level is None:
        level = settings.log_level

    if isinstance(level, int):
        return level

    normalized = level.upper()
    resolved = logging.getLevelName(normalized)
    if isinstance(resolved, int):
        return resolved
    raise ValueError(f"Unsupported log level: {level!r}")


def _build_formatter() -> logging.Formatter:
    return JsonContextFormatter(LOG_FORMAT, datefmt=DATE_FORMAT)


def _build_console_handler(level: int) -> logging.Handler:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(_build_formatter())
    return handler


def _build_file_handler(path: Path, level: int) -> logging.Handler:
    handler = RotatingFileHandler(
        path,
        maxBytes=MAX_LOG_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(_build_formatter())
    return handler


def get_logger(name: str = "website_knowledge_rag", level: int | str | None = None) -> logging.Logger:
    """
    Return a configured application logger.

    Safe to call repeatedly. The logger writes to stdout and `logs/app.log`,
    uses rotation to avoid unbounded log growth, and does not propagate to the
    root logger to prevent duplicate lines under Uvicorn or test runners.
    """

    resolved_level = _resolve_level(level)
    logger = logging.getLogger(name)
    logger.setLevel(resolved_level)

    if name not in _CONFIGURED_LOGGERS:
        logger.handlers.clear()
        logger.addHandler(_build_console_handler(resolved_level))
        logger.addHandler(_build_file_handler(APP_LOG_FILE, resolved_level))
        logger.propagate = False
        _CONFIGURED_LOGGERS.add(name)

    return logger


def get_crawl_logger(website_id: str, level: int | str | None = None) -> logging.Logger:
    """
    Return a per-website crawl logger.

    The logger also writes to stdout through the normal app logger style, but
    its file output is isolated at `logs/crawls/{website_id}.log`.
    """

    safe_id = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in website_id)
    logger_name = f"website_knowledge_rag.crawl.{safe_id}"
    resolved_level = _resolve_level(level)
    logger = logging.getLogger(logger_name)
    logger.setLevel(resolved_level)

    if logger_name not in _CONFIGURED_LOGGERS:
        logger.handlers.clear()
        logger.addHandler(_build_console_handler(resolved_level))
        logger.addHandler(_build_file_handler(CRAWL_LOG_DIR / f"{safe_id}.log", resolved_level))
        logger.propagate = False
        _CONFIGURED_LOGGERS.add(logger_name)

    return logger


def log_event(
    logger: logging.Logger,
    level: int | str,
    message: str,
    **context: Any,
) -> None:
    """
    Log a message with structured context.

    Example:
        log_event(logger, "INFO", "Crawled page", url=url, status_code=200)
    """

    logger.log(_resolve_level(level), message, extra={"context": context})
