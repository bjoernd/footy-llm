"""
Tests for the API client module.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

import pytest
import requests

from football_match_notification_service.api_client import (
    APIClientError,
    APIFootballClient,
    AuthenticationError,
    RateLimitError,
)
from football_match_notification_service.config_manager import ConfigManager


class TestAPIFootballClient:
    """Tests for the API-Football client."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration manager."""
        config = MagicMock(spec=ConfigManager)
        config.get.side_effect = lambda key: {
            "api_settings.base_url": "https://api-football-v1.p.rapidapi.com/v3",
            "api_settings.api_key": "test_api_key",
        }.get(key)
        config.get_with_default.return_value = 30
        return config

    @pytest.fixture
    def api_client(self, mock_config):
        """Create an API client with mock configuration."""
        return APIFootballClient(mock_config)

    def test_init_with_missing_base_url(self, mock_config):
        """Test initialization with missing base URL."""
        mock_config.get.side_effect = lambda key: None if key == "api_settings.base_url" else "test_api_key"
        with pytest.raises(ValueError, match="API base URL not configured"):
            APIFootballClient(mock_config)

    def test_init_with_missing_api_key(self, mock_config):
        """Test initialization with missing API key."""
        mock_config.get.side_effect = lambda key: "https://api-football-v1.p.rapidapi.com/v3" if key == "api_settings.base_url" else None
        with pytest.raises(ValueError, match="API key not configured"):
            APIFootballClient(mock_config)

    @patch("requests.get")
    def test_make_request_success(self, mock_get, api_client):
        """Test successful API request."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": [{"test": "data"}]}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Make request
        result = api_client._make_request("test_endpoint", {"param": "value"})

        # Verify request
        mock_get.assert_called_once_with(
            "https://api-football-v1.p.rapidapi.com/v3/test_endpoint",
            headers={
                "X-RapidAPI-Key": "test_api_key",
                "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
            },
            params={"param": "value"},
            timeout=30,
        )

        # Verify result
        assert result == {"response": [{"test": "data"}]}

    @patch("requests.get")
    def test_make_request_api_error(self, mock_get, api_client):
        """Test API error in response."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"errors": {"error": "Test error"}}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Make request and verify error
        with pytest.raises(APIClientError, match="API error: Test error"):
            api_client._make_request("test_endpoint")

    @patch("requests.get")
    def test_make_request_auth_error(self, mock_get, api_client):
        """Test authentication error."""
        # Mock response
        mock_response = MagicMock()
        mock_error = requests.exceptions.HTTPError()
        mock_error.response = MagicMock()
        mock_error.response.status_code = 401
        mock_response.raise_for_status.side_effect = mock_error
        mock_get.return_value = mock_response

        # Make request and verify error
        with pytest.raises(AuthenticationError, match="API authentication failed"):
            api_client._make_request("test_endpoint")

    @patch("requests.get")
    def test_make_request_rate_limit_error(self, mock_get, api_client):
        """Test rate limit error."""
        # Mock response
        mock_response = MagicMock()
        mock_error = requests.exceptions.HTTPError()
        mock_error.response = MagicMock()
        mock_error.response.status_code = 429
        mock_response.raise_for_status.side_effect = mock_error
        mock_get.return_value = mock_response

        # Make request and verify error
        with pytest.raises(RateLimitError, match="API rate limit exceeded"):
            api_client._make_request("test_endpoint")

    @patch("requests.get")
    def test_make_request_http_error(self, mock_get, api_client):
        """Test HTTP error."""
        # Mock response
        mock_response = MagicMock()
        mock_error = requests.exceptions.HTTPError("HTTP Error")
        mock_error.response = MagicMock()
        mock_error.response.status_code = 500
        mock_response.raise_for_status.side_effect = mock_error
        mock_get.return_value = mock_response

        # Make request and verify error
        with pytest.raises(APIClientError, match="HTTP error"):
            api_client._make_request("test_endpoint")

    @patch("requests.get")
    def test_make_request_connection_error(self, mock_get, api_client):
        """Test connection error."""
        # Mock error
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection Error")

        # Make request and verify error
        with pytest.raises(APIClientError, match="Request failed"):
            api_client._make_request("test_endpoint")

    @patch("requests.get")
    def test_make_request_json_error(self, mock_get, api_client):
        """Test JSON decode error."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("JSON Error", "", 0)
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Make request and verify error
        with pytest.raises(APIClientError, match="Invalid JSON response"):
            api_client._make_request("test_endpoint")

    @patch.object(APIFootballClient, "_make_request")
    def test_get_matches_by_team(self, mock_make_request, api_client):
        """Test get_matches_by_team method."""
        # Mock response
        mock_make_request.return_value = {"response": [{"fixture": {"id": 123}}]}

        # Call method
        result = api_client.get_matches_by_team("123", "2023-01-01", "2023-01-31")

        # Verify request
        mock_make_request.assert_called_once_with(
            "fixtures",
            {
                "team": "123",
                "from": "2023-01-01",
                "to": "2023-01-31",
                "timezone": "UTC",
            },
        )

        # Verify result
        assert result == {"response": [{"fixture": {"id": 123}}]}

    @patch.object(APIFootballClient, "_make_request")
    def test_get_match_details(self, mock_make_request, api_client):
        """Test get_match_details method."""
        # Mock response
        mock_make_request.return_value = {"response": [{"fixture": {"id": 123}}]}

        # Call method
        result = api_client.get_match_details("123")

        # Verify request
        mock_make_request.assert_called_once_with("fixtures", {"id": "123"})

        # Verify result
        assert result == {"response": [{"fixture": {"id": 123}}]}

    @patch.object(APIFootballClient, "_make_request")
    def test_get_live_matches(self, mock_make_request, api_client):
        """Test get_live_matches method."""
        # Mock response
        mock_make_request.return_value = {"response": [{"fixture": {"id": 123}}]}

        # Call method
        result = api_client.get_live_matches()

        # Verify request
        mock_make_request.assert_called_once_with("fixtures", {"live": "all"})

        # Verify result
        assert result == {"response": [{"fixture": {"id": 123}}]}
        
    @patch.object(APIFootballClient, "_make_request")
    def test_get_team_info(self, mock_make_request, api_client):
        """Test get_team_info method."""
        # Mock response
        mock_make_request.return_value = {"response": [{"team": {"id": 123}}]}

        # Call method
        result = api_client.get_team_info("123")

        # Verify request
        mock_make_request.assert_called_once_with("teams", {"id": "123"})

        # Verify result
        assert result == {"response": [{"team": {"id": 123}}]}
        
    @patch.object(APIFootballClient, "_make_request")
    def test_get_fixtures_events(self, mock_make_request, api_client):
        """Test get_fixtures_events method."""
        # Mock response
        mock_make_request.return_value = {"response": [{"event": "goal"}]}

        # Call method
        result = api_client.get_fixtures_events("123")

        # Verify request
        mock_make_request.assert_called_once_with("fixtures/events", {"fixture": "123"})

        # Verify result
        assert result == {"response": [{"event": "goal"}]}
        
    @patch.object(APIFootballClient, "_make_request")
    def test_get_fixtures_statistics(self, mock_make_request, api_client):
        """Test get_fixtures_statistics method."""
        # Mock response
        mock_make_request.return_value = {"response": [{"statistics": []}]}

        # Call method
        result = api_client.get_fixtures_statistics("123")

        # Verify request
        mock_make_request.assert_called_once_with("fixtures/statistics", {"fixture": "123"})

        # Verify result
        assert result == {"response": [{"statistics": []}]}
