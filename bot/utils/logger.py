import logging
import sys
from functools import lru_cache


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


@lru_cache(maxsize=1)
def configure_logging(level: str = "INFO") -> None:
    """Configure application-wide console logging once."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=LOG_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=False,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for a module."""
    configure_logging()
    return logging.getLogger(name)
