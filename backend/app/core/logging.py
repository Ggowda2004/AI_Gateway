import logging
import sys
import asyncio
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "gateway.log"

def setup_sync_logger():
    """
    we are setting up a unifies logger to our gateway
    """
    sync_logger = logging.getLogger("ai_gateway_sync")
    sync_logger.setLevel(logging.INFO)

    if sync_logger.handlers:
        return sync_logger
    
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    sync_logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )

    file_handler.setFormatter(formatter)
    sync_logger.addHandler(file_handler)

    return sync_logger

sync_logger = setup_sync_logger()

# The Async Wrapper Class

class AsyncLogger:
    """Non-blocking asynchronous wrapper over Python's standard logger."""
    async def info(self, msg: Any):
        await asyncio.to_thread(sync_logger.info, msg)
        # Offloads the blocking file-write call to a background thread pool

    async def warning(self, msg: Any):
        await asyncio.to_thread(sync_logger.warning, msg)

    async def error(self, msg: Any):
        await asyncio.to_thread(sync_logger.error, msg)

# Single async instance exported across the app
logger = AsyncLogger()