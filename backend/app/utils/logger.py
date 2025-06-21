"""
Logging configuration and utilities
"""
import logging
import logging.handlers
import json
from datetime import datetime
from pathlib import Path
import sys
import traceback
from typing import Any, Dict, Optional

from app.config.settings import settings

# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

class JSONFormatter(logging.Formatter):
    """
    Format log records as JSON
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)

def setup_logging(
    level: str = settings.LOGGING_LEVEL,
    log_to_file: bool = True,
    log_to_stdout: bool = True
) -> None:
    """
    Setup logging configuration
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Create formatters
    json_formatter = JSONFormatter()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Add file handler if enabled
    if log_to_file:
        # Regular log file
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=10485760,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setFormatter(json_formatter)
        root_logger.addHandler(file_handler)
        
        # Error log file
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / "error.log",
            maxBytes=10485760,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(json_formatter)
        root_logger.addHandler(error_handler)
    
    # Add stdout handler if enabled
    if log_to_stdout:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

class Logger:
    """
    Logger utility class with context
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _log(self, level: int, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Log message with extra context
        """
        if extra:
            kwargs["extra"] = {"extra_fields": extra}
        self.logger.log(level, msg, **kwargs)
    
    def debug(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        self._log(logging.DEBUG, msg, extra, **kwargs)
    
    def info(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        self._log(logging.INFO, msg, extra, **kwargs)
    
    def warning(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        self._log(logging.WARNING, msg, extra, **kwargs)
    
    def error(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        self._log(logging.ERROR, msg, extra, **kwargs)
    
    def critical(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        self._log(logging.CRITICAL, msg, extra, **kwargs)
    
    def exception(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Log exception with traceback
        """
        kwargs["exc_info"] = True
        self._log(logging.ERROR, msg, extra, **kwargs)

def get_logger(name: str) -> Logger:
    """
    Get logger instance
    """
    return Logger(name)

# Setup logging on module import
setup_logging()
