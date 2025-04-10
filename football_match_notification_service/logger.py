"""Logging system for Football Match Notification Service.

This module provides a customized logging system with console output,
file rotation, and custom log levels for match events.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Dict, Optional, Union


class FootballLogger:
    """Custom logger for Football Match Notification Service.

    This class provides a wrapper around Python's logging module with
    additional functionality specific to football match notifications.
    """

    # Default log format
    DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def __init__(
        self,
        name: str = "football_match_notification",
        log_level: int = logging.INFO,
        console_output: bool = True,
        log_file: Optional[str] = None,
        log_format: Optional[str] = None,
    ):
        """Initialize the logger.

        Args:
            name: Logger name.
            log_level: Logging level (default: INFO).
            console_output: Whether to output logs to console (default: True).
            log_file: Path to log file (default: None).
            log_format: Log message format (default: DEFAULT_FORMAT).
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        self.log_format = log_format or self.DEFAULT_FORMAT

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
        console_handler.setFormatter(logging.Formatter(self.log_format))
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
        file_handler.setFormatter(logging.Formatter(self.log_format))
        self.logger.addHandler(file_handler)

    def debug(self, message: str) -> None:
        """Log a debug message.

        Args:
            message: The message to log.
        """
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """Log an info message.

        Args:
            message: The message to log.
        """
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log a warning message.

        Args:
            message: The message to log.
        """
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log an error message.

        Args:
            message: The message to log.
        """
        self.logger.error(message)

    def critical(self, message: str) -> None:
        """Log a critical message.

        Args:
            message: The message to log.
        """
        self.logger.critical(message)
