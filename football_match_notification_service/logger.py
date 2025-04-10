"""Logging system for Football Match Notification Service.

This module provides a customized logging system with console output,
file rotation, and custom log levels for match events.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Dict, Optional, Union


# Custom log levels for match events
MATCH_START = 25
MATCH_END = 26
GOAL = 27
CARD = 28
SUBSTITUTION = 29
MATCH_EVENT = 30

# Register custom log levels with logging module
logging.addLevelName(MATCH_START, "MATCH_START")
logging.addLevelName(MATCH_END, "MATCH_END")
logging.addLevelName(GOAL, "GOAL")
logging.addLevelName(CARD, "CARD")
logging.addLevelName(SUBSTITUTION, "SUBSTITUTION")
logging.addLevelName(MATCH_EVENT, "MATCH_EVENT")


class FootballLogger:
    """Custom logger for Football Match Notification Service.

    This class provides a wrapper around Python's logging module with
    additional functionality specific to football match notifications.
    """

    # Default log format
    DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Default structured log format for JSON logging
    DEFAULT_STRUCTURED_FORMAT = {
        "timestamp": "%(asctime)s",
        "name": "%(name)s",
        "level": "%(levelname)s",
        "message": "%(message)s",
        "module": "%(module)s",
        "function": "%(funcName)s",
        "line": "%(lineno)d",
    }

    def __init__(
        self,
        name: str = "football_match_notification",
        log_level: int = logging.INFO,
        console_output: bool = True,
        log_file: Optional[str] = None,
        log_format: Optional[str] = None,
        structured_logging: bool = False,
    ):
        """Initialize the logger.

        Args:
            name: Logger name.
            log_level: Logging level (default: INFO).
            console_output: Whether to output logs to console (default: True).
            log_file: Path to log file (default: None).
            log_format: Log message format (default: DEFAULT_FORMAT).
            structured_logging: Whether to use structured logging (default: False).
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        self.log_format = log_format or self.DEFAULT_FORMAT
        self.structured_logging = structured_logging

        # Clear any existing handlers
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # Add console handler if requested
        if console_output:
            self._add_console_handler()

        # Add file handler if log file is specified
        if log_file:
            self._add_file_handler(log_file)

    def _add_console_handler(self) -> None:
        """Add a console handler to the logger."""
        console_handler = logging.StreamHandler(sys.stdout)
        
        if self.structured_logging:
            formatter = self._get_structured_formatter()
        else:
            formatter = logging.Formatter(self.log_format)
            
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _add_file_handler(self, log_file: str, max_bytes: int = 10485760, backup_count: int = 5) -> None:
        """Add a rotating file handler to the logger.

        Args:
            log_file: Path to log file.
            max_bytes: Maximum size of log file before rotation (default: 10MB).
            backup_count: Number of backup files to keep (default: 5).
        """
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        
        if self.structured_logging:
            formatter = self._get_structured_formatter()
        else:
            formatter = logging.Formatter(self.log_format)
            
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
    def _get_structured_formatter(self) -> logging.Formatter:
        """Get a JSON formatter for structured logging."""
        try:
            import json
            
            class JsonFormatter(logging.Formatter):
                def __init__(self, fmt_dict=None):
                    self.fmt_dict = fmt_dict if fmt_dict else self.DEFAULT_STRUCTURED_FORMAT
                    
                def format(self, record):
                    record_dict = self.fmt_dict.copy()
                    for key, value in record_dict.items():
                        try:
                            record_dict[key] = value % record.__dict__
                        except (KeyError, TypeError):
                            record_dict[key] = value
                            
                    # Add exception info if available
                    if record.exc_info:
                        record_dict["exception"] = self.formatException(record.exc_info)
                        
                    # Add extra fields from record
                    if hasattr(record, "extra"):
                        for key, value in record.extra.items():
                            record_dict[key] = value
                            
                    return json.dumps(record_dict)
                    
            return JsonFormatter(self.DEFAULT_STRUCTURED_FORMAT)
        except ImportError:
            # Fall back to standard formatter if json module is not available
            return logging.Formatter(self.log_format)

    def debug(self, message: str, extra: Optional[Dict] = None) -> None:
        """Log a debug message.

        Args:
            message: The message to log.
            extra: Extra fields to include in the log record.
        """
        self.logger.debug(message, extra={"extra": extra} if extra else None)

    def info(self, message: str, extra: Optional[Dict] = None) -> None:
        """Log an info message.

        Args:
            message: The message to log.
            extra: Extra fields to include in the log record.
        """
        self.logger.info(message, extra={"extra": extra} if extra else None)

    def warning(self, message: str, extra: Optional[Dict] = None) -> None:
        """Log a warning message.

        Args:
            message: The message to log.
            extra: Extra fields to include in the log record.
        """
        self.logger.warning(message, extra={"extra": extra} if extra else None)

    def error(self, message: str, extra: Optional[Dict] = None) -> None:
        """Log an error message.

        Args:
            message: The message to log.
            extra: Extra fields to include in the log record.
        """
        self.logger.error(message, extra={"extra": extra} if extra else None)

    def critical(self, message: str, extra: Optional[Dict] = None) -> None:
        """Log a critical message.

        Args:
            message: The message to log.
            extra: Extra fields to include in the log record.
        """
        self.logger.critical(message, extra={"extra": extra} if extra else None)
        
    # Custom log level methods for match events
    def match_start(self, message: str, extra: Optional[Dict] = None) -> None:
        """Log a match start event.

        Args:
            message: The message to log.
            extra: Extra fields to include in the log record.
        """
        self.logger.log(MATCH_START, message, extra={"extra": extra} if extra else None)
        
    def match_end(self, message: str, extra: Optional[Dict] = None) -> None:
        """Log a match end event.

        Args:
            message: The message to log.
            extra: Extra fields to include in the log record.
        """
        self.logger.log(MATCH_END, message, extra={"extra": extra} if extra else None)
        
    def goal(self, message: str, extra: Optional[Dict] = None) -> None:
        """Log a goal event.

        Args:
            message: The message to log.
            extra: Extra fields to include in the log record.
        """
        self.logger.log(GOAL, message, extra={"extra": extra} if extra else None)
        
    def card(self, message: str, extra: Optional[Dict] = None) -> None:
        """Log a card event.

        Args:
            message: The message to log.
            extra: Extra fields to include in the log record.
        """
        self.logger.log(CARD, message, extra={"extra": extra} if extra else None)
        
    def substitution(self, message: str, extra: Optional[Dict] = None) -> None:
        """Log a substitution event.

        Args:
            message: The message to log.
            extra: Extra fields to include in the log record.
        """
        self.logger.log(SUBSTITUTION, message, extra={"extra": extra} if extra else None)
        
    def match_event(self, message: str, extra: Optional[Dict] = None) -> None:
        """Log a generic match event.

        Args:
            message: The message to log.
            extra: Extra fields to include in the log record.
        """
        self.logger.log(MATCH_EVENT, message, extra={"extra": extra} if extra else None)
