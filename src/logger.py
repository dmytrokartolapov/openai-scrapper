import logging
import sys

from colorlog import ColoredFormatter


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

# Fallback formatter (no color)
PLAIN_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
plain_formatter = logging.Formatter(PLAIN_FORMAT)


class SafeColorHandler(logging.StreamHandler):
    """A handler that tries to use color, but falls back to plain formatting on KeyError."""

    def __init__(self, stream, color_formatter, plain_formatter):
        super().__init__(stream)
        self.color_formatter = color_formatter
        self.plain_formatter = plain_formatter

    def format(self, record):
        try:
            return self.color_formatter.format(record)
        except KeyError as e:
            if str(e) == "'log_color'":
                return self.plain_formatter.format(record)
            raise


def setup_logger() -> logging.Logger:
    """Configures the root logger, Uvicorn loggers, and a custom 'api' logger for consistent formatting and color.
    Returns the custom 'api' logger instance.
    """
    color_formatter = ColoredFormatter(LOG_FORMAT, datefmt=None, reset=True, log_colors=LOG_COLORS)

    logging.basicConfig(
        level=LOG_LEVEL,
        format=PLAIN_FORMAT,  # Use plain format for root logger
        stream=sys.stdout,
    )

    for logger_name in (LOGGER_NAME, "uvicorn", "uvicorn.error", "uvicorn.access", "httpx"):
        logger = logging.getLogger(logger_name)
        logger.handlers = []  # Remove default handlers
        handler = SafeColorHandler(sys.stdout, color_formatter, plain_formatter)
        logger.addHandler(handler)
        logger.setLevel(LOG_LEVEL)
        logger.propagate = False

    return logging.getLogger(LOGGER_NAME)
