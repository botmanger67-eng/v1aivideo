import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Import configuration – assume config.py contains a Config class or module-level constants.
# We'll handle missing imports gracefully for flexibility.
try:
    from config import Config
except ImportError:
    # Fallback settings if config is not available
    class Config:
        LOG_LEVEL: str = "DEBUG"
        LOG_DIR: str = "logs"
        LOG_FILE: str = "app.log"
        LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
        LOG_BACKUP_COUNT: int = 5
        LOG_CONSOLE: bool = True


def setup_logging(
    log_level: Optional[str] = None,
    log_dir: Optional[str] = None,
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
    max_bytes: Optional[int] = None,
    backup_count: Optional[int] = None,
    console: Optional[bool] = None,
) -> logging.Logger:
    """Configure the root logger with file and console handlers.

    Args:
        log_level: Logging level string (e.g., 'DEBUG', 'INFO').
        log_dir: Directory for log files.
        log_file: Base name of log file.
        log_format: Log message format string.
        max_bytes: Maximum size of a log file before rotation.
        backup_count: Number of backup log files to keep.
        console: Whether to add a console handler.

    Returns:
        The root logger after configuration.
    """
    try:
        # Retrieve settings from Config, environment, or defaults
        level = (log_level or os.environ.get("LOG_LEVEL") or Config.LOG_LEVEL).upper()
        log_dir = log_dir or os.environ.get("LOG_DIR") or Config.LOG_DIR
        log_file = log_file or os.environ.get("LOG_FILE") or Config.LOG_FILE
        log_format = log_format or os.environ.get("LOG_FORMAT") or Config.LOG_FORMAT
        max_bytes = max_bytes or int(os.environ.get("LOG_MAX_BYTES", Config.LOG_MAX_BYTES))
        backup_count = backup_count or int(os.environ.get("LOG_BACKUP_COUNT", Config.LOG_BACKUP_COUNT))
        console = console if console is not None else (
            os.environ.get("LOG_CONSOLE", "true").lower() == "true" if "LOG_CONSOLE" in os.environ
            else Config.LOG_CONSOLE
        )
    except Exception as e:
        # Fallback if any config retrieval fails
        level = "DEBUG"
        log_dir = "logs"
        log_file = "app.log"
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        max_bytes = 10 * 1024 * 1024
        backup_count = 5
        console = True
        logging.warning("Logger configuration error, using defaults: %s", e)

    # Create log directory if it doesn't exist
    try:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logging.error("Failed to create log directory '%s': %s", log_dir, e)
        log_dir = "."  # Fallback to current directory

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level, logging.DEBUG))

    # Prevent duplicate handlers
    if logger.handlers:
        logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(log_format)

    # File handler with rotation
    try:
        file_handler = RotatingFileHandler(
            Path(log_dir) / log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logging.error("Failed to create file handler: %s", e)

    # Console handler
    if console:
        try:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        except Exception as e:
            logging.error("Failed to create console handler: %s", e)

    # Optional: Set exception hook to log uncaught exceptions
    def exception_hook(exc_type, exc_value, exc_traceback):
        logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.excepthook = exception_hook

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module/name.

    This function ensures that the logging system is initialized at least once
    (e.g., on first call) and then returns a child logger for the given name.

    Args:
        name: The name for the logger, typically __name__ from the calling module.

    Returns:
        A configured logger instance.
    """
    # Ensure root logger is configured only once
    root = logging.getLogger()
    if not root.handlers:
        setup_logging()
    return logging.getLogger(name)


# Initialize root logging when module is imported (idempotent)
_log_initialized = False

def _initialize_logging_once():
    global _log_initialized
    if not _log_initialized:
        setup_logging()
        _log_initialized = True

_initialize_logging_once()