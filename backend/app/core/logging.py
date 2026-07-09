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

    if sync_logger.handlers:#prevent adding multiple handlers if the logger is already configured
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

#Wrapper Class

class AsyncLogger:
    """Non-blocking asynchronous wrapper over Python's standard logger."""
    async def info(self, msg: Any):
        await asyncio.to_thread(sync_logger.info, msg)
    async def warning(self, msg: Any):
        await asyncio.to_thread(sync_logger.warning, msg)
    async def error(self, msg: Any):
        await asyncio.to_thread(sync_logger.error, msg)
logger = AsyncLogger()


'''This code implements a non-blocking asynchronous wrapper around Python's standard logging library.
It uses asyncio.to_thread() to offload blocking file/console I/O operations to background threads, keeping the main event loop responsive.
The main asyncio event loop remains completely free to process other concurrent network requests or tasks without waiting for disk I/O operations to finish.'''