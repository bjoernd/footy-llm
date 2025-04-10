"""Configuration manager for Football Match Notification Service.

This module provides functionality to load, validate, and access configuration
from a JSON file.
"""

import json
import os
from typing import Any, Dict, List, Optional, Union


class ConfigValidationError(Exception):
    """Exception raised when configuration validation fails."""

    pass


class ConfigManager:
    """Manages configuration for the Football Match Notification Service.

    This class handles loading configuration from a JSON file, validating the
    configuration structure, and providing access to configuration values.
    """

    # Required configuration sections and fields
    REQUIRED_CONFIG = {
        "teams": ["name", "league", "team_id"],
        "api_settings": ["api_key", "base_url"],
        "notification_preferences": ["channels"],
        "polling_settings": ["frequency_normal"],
    }

    # Default values for optional configuration fields
    DEFAULT_CONFIG = {
        "api_settings": {
            "request_timeout": 30,
        },
        "polling_settings": {
            "frequency_during_match": 60,  # seconds
            "frequency_normal": 300,  # seconds
        },
        "notification_preferences": {
            "priority_order": ["email", "sms", "signal"],
        },
    }

    def __init__(self, config_path: str):
        """Initialize the configuration manager.

        Args:
            config_path: Path to the configuration file.
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from the specified JSON file.

        If the file doesn't exist or is invalid JSON, an empty configuration
        will be used.
        """
        if not os.path.exists(self.config_path):
            self.config = {}
            return

        try:
            with open(self.config_path, "r") as config_file:
                self.config = json.load(config_file)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading configuration: {e}")
            self.config = {}

    def validate_config(self) -> List[str]:
        """Validate the configuration structure.

        Returns:
            A list of validation errors. Empty list if validation passes.
        """
        errors = []

        # Check for required sections
        for section in self.REQUIRED_CONFIG:
            if section not in self.config:
                errors.append(f"Missing required section: {section}")
                continue

            # Check for required fields in each section
            for field in self.REQUIRED_CONFIG[section]:
                if section == "teams":
                    # Teams is a list of dictionaries
                    if not isinstance(self.config[section], list):
                        errors.append(f"Section '{section}' must be a list")
                        continue

                    for i, team in enumerate(self.config[section]):
                        if not isinstance(team, dict):
                            errors.append(f"Team at index {i} must be a dictionary")
                            continue
                        if field not in team:
                            errors.append(f"Team at index {i} missing required field: {field}")
                else:
                    # Other sections are dictionaries
                    if not isinstance(self.config[section], dict):
                        errors.append(f"Section '{section}' must be a dictionary")
                        continue
                    if field not in self.config[section]:
                        errors.append(f"Section '{section}' missing required field: {field}")

        return errors
