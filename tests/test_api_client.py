"""
Tests for the API client module.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

import pytest
import requests

from football_match_notification_service.api_client import (
    APIClient,
    APIClientError,
    AuthenticationError,
    FootballDataClient,
    RateLimitError,
)
from football_match_notification_service.config_manager import ConfigManager


class TestAPIClient(unittest.TestCase):
    """Test cases for the API client."""

    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = MagicMock(spec=ConfigManager)
        self.config_manager.get.side_effect = self._mock_config_get

    def _mock_config_get(self, key, default=None):
        """Mock implementation of config_manager.get."""
        config_values = {
            "api.football_data.base_url": "https://api.football-data.org/v4",
            "api.football_data.timeout": 30,
            "api.football_data.api_key": "test-api-key",
        }
        return config_values.get(key, default)

    @patch("football_match_notification_service.api_client.requests.get")
    def test_make_request_success(self, mock_get):
        """Test successful API request."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response

        # Create client and make request
        client = FootballDataClient(self.config_manager)
        result = client._make_request("/test")

        # Verify request was made correctly
        mock_get.assert_called_once_with(
            "https://api.football-data.org/v4/test",
            headers={"X-Auth-Token": "test-api-key", "Accept": "application/json"},
            params=None,
            timeout=30,
        )

        # Verify result
        assert result == {"data": "test"}

    @patch("football_match_notification_service.api_client.requests.get")
    def test_authentication_error(self, mock_get):
        """Test authentication error handling."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response

        # Create client and attempt request
        client = FootballDataClient(self.config_manager)

        # Verify exception is raised
        with pytest.raises(AuthenticationError):
            client._make_request("/test")

    @patch("football_match_notification_service.api_client.requests.get")
    def test_rate_limit_error(self, mock_get):
        """Test rate limit error handling."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Too Many Requests"
        mock_get.return_value = mock_response

        # Create client and attempt request
        client = FootballDataClient(self.config_manager)

        # Verify exception is raised
        with pytest.raises(RateLimitError):
            client._make_request("/test")

    @patch("football_match_notification_service.api_client.requests.get")
    def test_api_error(self, mock_get):
        """Test general API error handling."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        # Create client and attempt request
        client = FootballDataClient(self.config_manager)

        # Verify exception is raised
        with pytest.raises(APIClientError):
            client._make_request("/test")

    @patch("football_match_notification_service.api_client.requests.get")
    def test_json_decode_error(self, mock_get):
        """Test JSON decode error handling."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON"
        mock_get.return_value = mock_response

        # Create client and attempt request
        client = FootballDataClient(self.config_manager)

        # Verify exception is raised
        with pytest.raises(APIClientError):
            client._make_request("/test")

    @patch("football_match_notification_service.api_client.requests.get")
    def test_request_exception(self, mock_get):
        """Test request exception handling."""
        # Setup mock to raise exception
        mock_get.side_effect = requests.RequestException("Connection error")

        # Create client and attempt request
        client = FootballDataClient(self.config_manager)

        # Verify exception is raised
        with pytest.raises(APIClientError):
            client._make_request("/test")

    @patch("football_match_notification_service.api_client.requests.get")
    def test_get_matches(self, mock_get):
        """Test get_matches method."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"matches": []}
        mock_get.return_value = mock_response

        # Create client and make request
        client = FootballDataClient(self.config_manager)
        result = client.get_matches(
            team_id="123", date_from="2025-04-01", date_to="2025-04-10"
        )

        # Verify request was made correctly
        mock_get.assert_called_once_with(
            "https://api.football-data.org/v4/matches",
            headers={"X-Auth-Token": "test-api-key", "Accept": "application/json"},
            params={"team": "123", "dateFrom": "2025-04-01", "dateTo": "2025-04-10"},
            timeout=30,
        )

        # Verify result
        assert result == {"matches": []}

    @patch("football_match_notification_service.api_client.requests.get")
    def test_get_match_details(self, mock_get):
        """Test get_match_details method."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"match": {"id": "123"}}
        mock_get.return_value = mock_response

        # Create client and make request
        client = FootballDataClient(self.config_manager)
        result = client.get_match_details("123")

        # Verify request was made correctly
        mock_get.assert_called_once_with(
            "https://api.football-data.org/v4/matches/123",
            headers={"X-Auth-Token": "test-api-key", "Accept": "application/json"},
            params=None,
            timeout=30,
        )

        # Verify result
        assert result == {"match": {"id": "123"}}

    def test_missing_api_key(self):
        """Test error handling when API key is missing."""
        # Setup config manager to return None for API key
        config_manager = MagicMock(spec=ConfigManager)
        config_manager.get.side_effect = lambda key, default=None: (
            None
            if key == "api.football_data.api_key"
            else self._mock_config_get(key, default)
        )

        # Create client
        client = FootballDataClient(config_manager)

        # Verify exception is raised when trying to get headers
        with pytest.raises(AuthenticationError):
            client._get_headers()
