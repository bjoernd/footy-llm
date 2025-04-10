"""Tests for the logging system."""

import json
import logging
import os
import tempfile
from unittest.mock import patch

import pytest

from football_match_notification_service.logger import (
    CARD,
    GOAL,
    MATCH_END,
    MATCH_EVENT,
    MATCH_START,
    SUBSTITUTION,
    FootballLogger,
)


class TestFootballLogger:
    """Test cases for the FootballLogger class."""

    def test_init_default(self):
        """Test initializing logger with default parameters."""
        logger = FootballLogger()
        assert logger.logger.name == "football_match_notification"
        assert logger.logger.level == logging.INFO
        assert logger.log_format == logger.DEFAULT_FORMAT
        assert logger.structured_logging is False
        assert len(logger.logger.handlers) == 1  # Console handler

    def test_init_custom(self):
        """Test initializing logger with custom parameters."""
        logger = FootballLogger(
            name="test_logger",
            log_level=logging.DEBUG,
            console_output=False,
            structured_logging=True,
        )
        assert logger.logger.name == "test_logger"
        assert logger.logger.level == logging.DEBUG
        assert logger.structured_logging is True
        assert len(logger.logger.handlers) == 0  # No handlers

    def test_console_handler(self):
        """Test adding console handler."""
        logger = FootballLogger(console_output=True)
        assert len(logger.logger.handlers) == 1
        assert isinstance(logger.logger.handlers[0], logging.StreamHandler)

    def test_file_handler(self):
        """Test adding file handler."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")
            logger = FootballLogger(console_output=False, log_file=log_file)
            assert len(logger.logger.handlers) == 1
            assert isinstance(logger.logger.handlers[0], logging.handlers.RotatingFileHandler)

    def test_both_handlers(self):
        """Test adding both console and file handlers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")
            logger = FootballLogger(console_output=True, log_file=log_file)
            assert len(logger.logger.handlers) == 2
            assert isinstance(logger.logger.handlers[0], logging.StreamHandler)
            assert isinstance(logger.logger.handlers[1], logging.handlers.RotatingFileHandler)

    def test_log_methods(self):
        """Test standard log methods."""
        logger = FootballLogger(console_output=False)
        
        with patch.object(logger.logger, "debug") as mock_debug:
            logger.debug("Debug message")
            mock_debug.assert_called_once_with("Debug message", extra=None)
            
        with patch.object(logger.logger, "info") as mock_info:
            logger.info("Info message")
            mock_info.assert_called_once_with("Info message", extra=None)
            
        with patch.object(logger.logger, "warning") as mock_warning:
            logger.warning("Warning message")
            mock_warning.assert_called_once_with("Warning message", extra=None)
            
        with patch.object(logger.logger, "error") as mock_error:
            logger.error("Error message")
            mock_error.assert_called_once_with("Error message", extra=None)
            
        with patch.object(logger.logger, "critical") as mock_critical:
            logger.critical("Critical message")
            mock_critical.assert_called_once_with("Critical message", extra=None)

    def test_custom_log_levels(self):
        """Test custom log level methods."""
        logger = FootballLogger(console_output=False)
        
        with patch.object(logger.logger, "log") as mock_log:
            logger.match_start("Match started")
            mock_log.assert_called_once_with(MATCH_START, "Match started", extra=None)
            mock_log.reset_mock()
            
            logger.match_end("Match ended")
            mock_log.assert_called_once_with(MATCH_END, "Match ended", extra=None)
            mock_log.reset_mock()
            
            logger.goal("Goal scored")
            mock_log.assert_called_once_with(GOAL, "Goal scored", extra=None)
            mock_log.reset_mock()
            
            logger.card("Card shown")
            mock_log.assert_called_once_with(CARD, "Card shown", extra=None)
            mock_log.reset_mock()
            
            logger.substitution("Player substituted")
            mock_log.assert_called_once_with(SUBSTITUTION, "Player substituted", extra=None)
            mock_log.reset_mock()
            
            logger.match_event("Generic match event")
            mock_log.assert_called_once_with(MATCH_EVENT, "Generic match event", extra=None)

    def test_extra_fields(self):
        """Test logging with extra fields."""
        logger = FootballLogger(console_output=False)
        extra = {"team": "Arsenal", "score": "1-0"}
        
        with patch.object(logger.logger, "info") as mock_info:
            logger.info("Goal scored", extra=extra)
            mock_info.assert_called_once_with("Goal scored", extra={"extra": extra})

    def test_structured_logging(self):
        """Test structured logging format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")
            logger = FootballLogger(
                console_output=False,
                log_file=log_file,
                structured_logging=True,
            )
            
            # Log a message
            logger.info("Test message", extra={"team": "Arsenal"})
            
            # Read the log file
            with open(log_file, "r") as f:
                log_content = f.read().strip()
            
            # Parse JSON
            log_entry = json.loads(log_content)
            
            # Check fields
            assert log_entry["message"] == "Test message"
            assert log_entry["level"] == "INFO"
            assert log_entry["name"] == "football_match_notification"
            assert "timestamp" in log_entry
            assert log_entry["team"] == "Arsenal"
