"""Configuration manager for Football Match Notification Service.

This module provides functionality to load, validate, and access configuration
from a JSON file.
"""

import json
import os
from typing import Any, Dict, Optional


class ConfigManager:
    """Manages configuration for the Football Match Notification Service.

    This class handles loading configuration from a JSON file, validating the
    configuration structure, and providing access to configuration values.
    """

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
