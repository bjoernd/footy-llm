"""Tests for the configuration manager."""

import json
import os
import tempfile
from unittest import mock

import pytest

from football_match_notification_service.config_manager import ConfigManager, ConfigValidationError


class TestConfigManager:
    """Test cases for the ConfigManager class."""

    def test_load_config_file_not_exists(self):
        """Test loading configuration when file doesn't exist."""
        with tempfile.NamedTemporaryFile(delete=True) as temp:
            # Delete the file to ensure it doesn't exist
            temp_path = temp.name
        
        # File should not exist at this point
        assert not os.path.exists(temp_path)
        
        # Initialize config manager with non-existent file
        config_manager = ConfigManager(temp_path)
        
        # Config should be empty
        assert config_manager.config == {}

    def test_load_config_invalid_json(self):
        """Test loading configuration with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp:
            temp.write("This is not valid JSON")
            temp_path = temp.name
        
        try:
            # Initialize config manager with invalid JSON file
            config_manager = ConfigManager(temp_path)
            
            # Config should be empty due to JSON error
            assert config_manager.config == {}
        finally:
            # Clean up
            os.unlink(temp_path)

    def test_load_config_valid_json(self):
        """Test loading configuration with valid JSON."""
        test_config = {
            "teams": [
                {
                    "name": "Test Team",
                    "league": "Test League",
                    "team_id": "123"
                }
            ],
            "api_settings": {
                "api_key": "test_key",
                "base_url": "https://test.api"
            },
            "notification_preferences": {
                "channels": ["email"]
            },
            "polling_settings": {
                "frequency_normal": 300
            }
        }
        
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp:
            json.dump(test_config, temp)
            temp_path = temp.name
        
        try:
            # Initialize config manager with valid JSON file
            config_manager = ConfigManager(temp_path)
            
            # Config should match the test config
            assert config_manager.config == test_config
        finally:
            # Clean up
            os.unlink(temp_path)

    def test_validate_config_valid(self):
        """Test validating a valid configuration."""
        test_config = {
            "teams": [
                {
                    "name": "Test Team",
                    "league": "Test League",
                    "team_id": "123"
                }
            ],
            "api_settings": {
                "api_key": "test_key",
                "base_url": "https://test.api"
            },
            "notification_preferences": {
                "channels": ["email"]
            },
            "polling_settings": {
                "frequency_normal": 300
            }
        }
        
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp:
            json.dump(test_config, temp)
            temp_path = temp.name
        
        try:
            # Initialize config manager with valid config
            config_manager = ConfigManager(temp_path)
            
            # Validation should pass with no errors
            errors = config_manager.validate_config()
            assert len(errors) == 0
            
            # ensure_valid_config should not raise an exception
            config_manager.ensure_valid_config()
        finally:
            # Clean up
            os.unlink(temp_path)

    def test_validate_config_missing_section(self):
        """Test validating a configuration with missing sections."""
        test_config = {
            "teams": [
                {
                    "name": "Test Team",
                    "league": "Test League",
                    "team_id": "123"
                }
            ],
            # Missing api_settings
            "notification_preferences": {
                "channels": ["email"]
            },
            # Missing polling_settings
        }
        
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp:
            json.dump(test_config, temp)
            temp_path = temp.name
        
        try:
            # Initialize config manager with invalid config
            config_manager = ConfigManager(temp_path)
            
            # Validation should fail with errors
            errors = config_manager.validate_config()
            assert len(errors) == 2
            assert "Missing required section: api_settings" in errors
            assert "Missing required section: polling_settings" in errors
            
            # ensure_valid_config should raise an exception
            with pytest.raises(ConfigValidationError):
                config_manager.ensure_valid_config()
        finally:
            # Clean up
            os.unlink(temp_path)

    def test_validate_config_missing_fields(self):
        """Test validating a configuration with missing fields."""
        test_config = {
            "teams": [
                {
                    "name": "Test Team",
                    # Missing league
                    "team_id": "123"
                }
            ],
            "api_settings": {
                "api_key": "test_key",
                # Missing base_url
            },
            "notification_preferences": {
                # Missing channels
            },
            "polling_settings": {
                # Missing frequency_normal
            }
        }
        
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp:
            json.dump(test_config, temp)
            temp_path = temp.name
        
        try:
            # Initialize config manager with invalid config
            config_manager = ConfigManager(temp_path)
            
            # Validation should fail with errors
            errors = config_manager.validate_config()
            assert len(errors) == 4
            assert "Team at index 0 missing required field: league" in errors
            assert "Section 'api_settings' missing required field: base_url" in errors
            assert "Section 'notification_preferences' missing required field: channels" in errors
            assert "Section 'polling_settings' missing required field: frequency_normal" in errors
        finally:
            # Clean up
            os.unlink(temp_path)

    def test_get_config_value(self):
        """Test getting configuration values."""
        test_config = {
            "teams": [
                {
                    "name": "Test Team",
                    "league": "Test League",
                    "team_id": "123"
                }
            ],
            "api_settings": {
                "api_key": "test_key",
                "base_url": "https://test.api",
                "nested": {
                    "value": "nested_value"
                }
            },
            "notification_preferences": {
                "channels": ["email"]
            },
            "polling_settings": {
                "frequency_normal": 300
            }
        }
        
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp:
            json.dump(test_config, temp)
            temp_path = temp.name
        
        try:
            # Initialize config manager with test config
            config_manager = ConfigManager(temp_path)
            
            # Test getting top-level values
            assert config_manager.get("teams") == test_config["teams"]
            
            # Test getting nested values with dot notation
            assert config_manager.get("api_settings.api_key") == "test_key"
            assert config_manager.get("api_settings.nested.value") == "nested_value"
            
            # Test getting non-existent values
            assert config_manager.get("non_existent") is None
            assert config_manager.get("non_existent", "default") == "default"
            assert config_manager.get("api_settings.non_existent") is None
            assert config_manager.get("api_settings.non_existent", "default") == "default"
        finally:
            # Clean up
            os.unlink(temp_path)

    def test_get_with_default_config(self):
        """Test getting values with fallback to default config."""
        test_config = {
            "teams": [
                {
                    "name": "Test Team",
                    "league": "Test League",
                    "team_id": "123"
                }
            ],
            "api_settings": {
                "api_key": "test_key",
                "base_url": "https://test.api"
                # request_timeout not specified, should use default
            },
            "notification_preferences": {
                "channels": ["email"]
                # priority_order not specified, should use default
            },
            "polling_settings": {
                "frequency_normal": 300
                # frequency_during_match not specified, should use default
            }
        }
        
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp:
            json.dump(test_config, temp)
            temp_path = temp.name
        
        try:
            # Initialize config manager with test config
            config_manager = ConfigManager(temp_path)
            
            # Apply defaults
            config_manager._apply_defaults()
            
            # Test getting values with defaults
            assert config_manager.get_with_default("api_settings.request_timeout") == 30
            assert config_manager.get_with_default("polling_settings.frequency_during_match") == 60
            assert config_manager.get_with_default("notification_preferences.priority_order") == ["email", "sms", "signal"]
            
            # Test getting user-specified values
            assert config_manager.get_with_default("api_settings.api_key") == "test_key"
            assert config_manager.get_with_default("polling_settings.frequency_normal") == 300
        finally:
            # Clean up
            os.unlink(temp_path)

    def test_reload_config(self):
        """Test reloading configuration."""
        initial_config = {
            "teams": [
                {
                    "name": "Initial Team",
                    "league": "Initial League",
                    "team_id": "123"
                }
            ],
            "api_settings": {
                "api_key": "initial_key",
                "base_url": "https://initial.api"
            },
            "notification_preferences": {
                "channels": ["email"]
            },
            "polling_settings": {
                "frequency_normal": 300
            }
        }
        
        updated_config = {
            "teams": [
                {
                    "name": "Updated Team",
                    "league": "Updated League",
                    "team_id": "456"
                }
            ],
            "api_settings": {
                "api_key": "updated_key",
                "base_url": "https://updated.api"
            },
            "notification_preferences": {
                "channels": ["sms"]
            },
            "polling_settings": {
                "frequency_normal": 600
            }
        }
        
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp:
            json.dump(initial_config, temp)
            temp_path = temp.name
        
        try:
            # Initialize config manager with initial config
            config_manager = ConfigManager(temp_path)
            
            # Verify initial config is loaded
            assert config_manager.get("teams")[0]["name"] == "Initial Team"
            
            # Update the config file
            with open(temp_path, "w") as f:
                json.dump(updated_config, f)
            
            # Reload the config
            result = config_manager.reload()
            assert result is True
            
            # Verify updated config is loaded
            assert config_manager.get("teams")[0]["name"] == "Updated Team"
            
            # Test reload with invalid JSON
            with open(temp_path, "w") as f:
                f.write("This is not valid JSON")
            
            # Reload should fail and keep old config
            result = config_manager.reload()
            assert result is False
            
            # Config should still have the updated values
            assert config_manager.get("teams")[0]["name"] == "Updated Team"
        finally:
            # Clean up
            os.unlink(temp_path)
