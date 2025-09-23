"""
Logging configuration and setup utilities.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

import structlog
from rich.console import Console
from rich.logging import RichHandler

from config import LoggingConfig


def setup_logging(config: LoggingConfig, logger_name: Optional[str] = None) -> logging.Logger:
    """
    Setup structured logging with both file and console output.

    Args:
        config: Logging configuration
        logger_name: Optional logger name, defaults to root logger

    Returns:
        Configured logger instance
    """
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Get logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, config.level.upper()))

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler with Rich formatting
    console_handler = RichHandler(
        console=Console(stderr=True),
        show_time=True,
        show_path=True,
        markup=True,
        rich_tracebacks=True
    )
    console_handler.setLevel(getattr(logging, config.level.upper()))

    console_formatter = logging.Formatter(
        fmt="%(message)s",
        datefmt="[%X]"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler if configured
    if config.log_file:
        config.log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            filename=config.log_file,
            maxBytes=config.max_file_size,
            backupCount=config.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        file_formatter = logging.Formatter(
            fmt=config.format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name

    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin class to add logging capability to any class."""

    @property
    def logger(self) -> structlog.BoundLogger:
        """Get logger for this class."""
        return get_logger(self.__class__.__name__)


def log_function_call(func):
    """Decorator to log function calls and execution time."""
    import functools
    import time

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()

        logger.info(
            "Function called",
            function=func.__name__,
            args_count=len(args),
            kwargs_keys=list(kwargs.keys())
        )

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            logger.info(
                "Function completed",
                function=func.__name__,
                execution_time=execution_time,
                success=True
            )

            return result

        except Exception as e:
            execution_time = time.time() - start_time

            logger.error(
                "Function failed",
                function=func.__name__,
                execution_time=execution_time,
                error=str(e),
                error_type=type(e).__name__,
                success=False
            )
            raise

    return wrapper