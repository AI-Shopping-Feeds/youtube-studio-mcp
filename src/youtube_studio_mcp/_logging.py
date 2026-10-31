"""Stdlib logging for youtube-studio-mcp. Logs go to stderr so stdio stays clean for JSON-RPC."""

from __future__ import annotations

import logging
import os
import sys

LOGGER_NAME = "youtube_studio_mcp"


def get_logger(name: str | None = None) -> logging.Logger:
    base = logging.getLogger(LOGGER_NAME)
    if not base.handlers:
        configure_default()
    if name and name != LOGGER_NAME:
        return base.getChild(name)
    return base


def configure_default() -> None:
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    logger.addHandler(handler)
    level = os.environ.get("YOUTUBE_LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, level, logging.INFO))
    logger.propagate = False
