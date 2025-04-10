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
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.

        Args:
            key: The configuration key to retrieve. Can use dot notation for nested keys.
            default: The default value to return if the key is not found.

        Returns:
            The configuration value or the default if not found.
        """
        if not key:
            return default

        # Handle nested keys with dot notation
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if not isinstance(value, dict) or k not in value:
                return default
            value = value[k]
            
        return value
    
    def get_with_default(self, key: str) -> Any:
        """Get a configuration value with fallback to DEFAULT_CONFIG.

        Args:
            key: The configuration key to retrieve. Can use dot notation for nested keys.

        Returns:
            The configuration value, the default from DEFAULT_CONFIG, or None if not found.
        """
        # First try to get from user config
        value = self.get(key)
        if value is not None:
            return value
            
        # If not found, try to get from DEFAULT_CONFIG
        keys = key.split(".")
        default_value = self.DEFAULT_CONFIG
        
        for k in keys:
            if not isinstance(default_value, dict) or k not in default_value:
                return None
            default_value = default_value[k]
            
        return default_value
    
    def reload(self) -> bool:
        """Reload configuration from the file.

        Returns:
            True if configuration was successfully reloaded, False otherwise.
        """
        old_config = self.config.copy()
        self.load_config()
        
        # Check if config was actually loaded
        if not self.config and old_config:
            # Restore old config if new one is empty
            self.config = old_config
            return False
            
        return True
    
    def ensure_valid_config(self) -> None:
        """Ensure the configuration is valid.

        Raises:
            ConfigValidationError: If the configuration is invalid.
        """
        errors = self.validate_config()
        if errors:
            error_message = "\n".join(errors)
            raise ConfigValidationError(f"Invalid configuration:\n{error_message}")
            
        # Apply default values for missing optional fields
        self._apply_defaults()
    
    def _apply_defaults(self) -> None:
        """Apply default values for missing optional configuration fields."""
        for section, defaults in self.DEFAULT_CONFIG.items():
            if section not in self.config:
                self.config[section] = {}
                
            for key, value in defaults.items():
                if key not in self.config[section]:
                    self.config[section][key] = value
