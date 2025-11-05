"""
Logging configuration for Project Handler.
Provides structured logging capabilities across the application.
"""
import logging
import sys
from typing import Any
from src.core.config import get_settings


def setup_logging() -> logging.Logger:
    """
    Configure and return application logger.

    Returns:
        logging.Logger: Configured logger instance
    """
    settings = get_settings()

    # Create logger
    logger = logging.getLogger("project_handler")
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "project_handler") -> logging.Logger:
    """
    Get logger instance by name.

    Args:
        name: Logger name

    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


# Initialize default logger
logger = setup_logging()
