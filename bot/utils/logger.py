import sys
from loguru import logger
from config import settings

logger.remove()

log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

logger.add(
    sys.stdout,
    format=log_format,
    level=settings.LOG_LEVEL,
    colorize=True,
)

logger.add(
    "logs/bot_{time:YYYY-MM-DD}.log",
    format=log_format,
    level="DEBUG",
    rotation="1 day",
    retention="7 days",
    compression="zip",
)

__all__ = ["logger"]
