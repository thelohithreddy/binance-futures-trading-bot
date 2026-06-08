"""Centralized logging configuration for the trading bot."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class StructuredFormatter(logging.Formatter):
    """Formatter that emits Timestamp | Level | Event | Details."""

    def format(self, record: logging.LogRecord) -> str:
        event = getattr(record, "event", "general")
        timestamp = self.formatTime(record, self.datefmt)
        return f"{timestamp} | {record.levelname} | {event} | {record.getMessage()}"


class EventAdapter(logging.LoggerAdapter):
    """Logger adapter that injects a structured event field."""

    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        extra = kwargs.setdefault("extra", {})
        extra.setdefault("event", self.extra.get("event", "general"))
        return msg, kwargs


def setup_logging(*, log_level: str, log_file: str) -> None:
    """Configure root logging for console and rotating file output."""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)

    formatter = StructuredFormatter(datefmt=DATE_FORMAT)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.WARNING)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("binance").setLevel(logging.WARNING)


def get_logger(name: str, *, event: str) -> EventAdapter:
    """Return a logger adapter tagged with a default event name."""
    base_logger = logging.getLogger(name)
    return EventAdapter(base_logger, {"event": event})
