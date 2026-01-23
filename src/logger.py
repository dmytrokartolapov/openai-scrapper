import logging
import sys

try:
    from colorlog import ColoredFormatter
except ImportError:
    raise ImportError("Please install colorlog: pip install colorlog")

LOGGER_NAME = "api"
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(log_color)s%(asctime)s | %(levelname)s | %(name)s | %(message)s"
LOG_COLORS = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}


def setup_logger() -> logging.Logger:
    """Configures the root logger, Uvicorn loggers, and a custom 'api' logger for consistent formatting and color.
    Returns the custom 'api' logger instance.
    Usage example:
    from logger import setup_logger
    logger = setup_logger()
    logger.info("This is a colored log message from the API logger.")
    """
    formatter = ColoredFormatter(LOG_FORMAT, datefmt=None, reset=True, log_colors=LOG_COLORS)
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        stream=sys.stdout,
    )

    for logger_name in (LOGGER_NAME, "uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        logger.handlers = []  # Remove default handlers
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(LOG_LEVEL)
        logger.propagate = False

    return logging.getLogger(LOGGER_NAME)
