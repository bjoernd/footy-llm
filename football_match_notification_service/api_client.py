"""
API Client module for Football Match Notification Service.

This module provides an abstract base class for API clients and a concrete implementation
for the API-Football.com API via RapidAPI.
"""

import abc
import json
import logging
from typing import Any, Dict, Optional, Union

import requests

from football_match_notification_service.config_manager import ConfigManager
from football_match_notification_service.logger import get_logger

# Set up logger
logger = get_logger(__name__)


class APIClientError(Exception):
    """Base exception for API client errors."""

    pass


class AuthenticationError(APIClientError):
    """Exception raised for authentication errors."""

    pass


class RateLimitError(APIClientError):
    """Exception raised when API rate limit is exceeded."""

    pass


class APIClient(abc.ABC):
    """Abstract base class for API clients."""

    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the API client.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager

    @abc.abstractmethod
    def get_matches_by_team(self, team_id: str, from_date: str, to_date: str) -> Dict:
        """
        Get matches for a specific team within a date range.

        Args:
            team_id: Team identifier
            from_date: Start date in format YYYY-MM-DD
            to_date: End date in format YYYY-MM-DD

        Returns:
            Dict containing match data

        Raises:
            APIClientError: If the API request fails
        """
        pass

    @abc.abstractmethod
    def get_match_details(self, match_id: str) -> Dict:
        """
        Get detailed information for a specific match.

        Args:
            match_id: Match identifier

        Returns:
            Dict containing match details

        Raises:
            APIClientError: If the API request fails
        """
        pass

    @abc.abstractmethod
    def get_live_matches(self) -> Dict:
        """
        Get all currently live matches.

        Returns:
            Dict containing live match data

        Raises:
            APIClientError: If the API request fails
        """
        pass


class APIFootballClient(APIClient):
    """Client for the API-Football.com API via RapidAPI."""

    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the API-Football client.

        Args:
            config_manager: Configuration manager instance
        """
        super().__init__(config_manager)
        self.base_url = self.config_manager.get("api_settings.base_url")
        self.api_key = self.config_manager.get("api_settings.api_key")
        self.timeout = self.config_manager.get_with_default("api_settings.request_timeout")
        
        if not self.base_url:
            raise ValueError("API base URL not configured")
        if not self.api_key:
            raise ValueError("API key not configured")

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make a request to the API-Football API.

        Args:
            endpoint: API endpoint to call
            params: Query parameters for the request

        Returns:
            Dict containing the API response

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit is exceeded
            APIClientError: For other API errors
        """
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }

        try:
            logger.debug(f"Making API request to {endpoint}", extra={"params": params})
            response = requests.get(
                url, headers=headers, params=params, timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            # API-Football returns errors in the response body
            if "errors" in data and data["errors"]:
                error_msg = ", ".join(str(err) for err in data["errors"].values())
                raise APIClientError(f"API error: {error_msg}")
                
            return data
            
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 401:
                    raise AuthenticationError("API authentication failed") from e
                elif e.response.status_code == 429:
                    raise RateLimitError("API rate limit exceeded") from e
            raise APIClientError(f"HTTP error: {e}") from e
        except requests.exceptions.RequestException as e:
            raise APIClientError(f"Request failed: {e}") from e
        except json.JSONDecodeError as e:
            raise APIClientError(f"Invalid JSON response: {e}") from e

    def get_matches_by_team(self, team_id: str, from_date: str, to_date: str) -> Dict:
        """
        Get matches for a specific team within a date range.

        Args:
            team_id: Team identifier
            from_date: Start date in format YYYY-MM-DD
            to_date: End date in format YYYY-MM-DD

        Returns:
            Dict containing match data

        Raises:
            APIClientError: If the API request fails
        """
        params = {
            "team": team_id,
            "from": from_date,
            "to": to_date,
            "timezone": "UTC"
        }
        return self._make_request("fixtures", params)

    def get_match_details(self, match_id: str) -> Dict:
        """
        Get detailed information for a specific match.

        Args:
            match_id: Match identifier

        Returns:
            Dict containing match details

        Raises:
            APIClientError: If the API request fails
        """
        params = {"id": match_id}
        return self._make_request("fixtures", params)

    def get_live_matches(self) -> Dict:
        """
        Get all currently live matches.

        Returns:
            Dict containing live match data

        Raises:
            APIClientError: If the API request fails
        """
        params = {"live": "all"}
        return self._make_request("fixtures", params)
        
    def get_team_info(self, team_id: str) -> Dict:
        """
        Get information about a specific team.
        
        Args:
            team_id: Team identifier
            
        Returns:
            Dict containing team information
            
        Raises:
            APIClientError: If the API request fails
        """
        params = {"id": team_id}
        return self._make_request("teams", params)
        
    def get_fixtures_events(self, fixture_id: str) -> Dict:
        """
        Get events for a specific fixture/match.
        
        Args:
            fixture_id: Fixture/match identifier
            
        Returns:
            Dict containing fixture events
            
        Raises:
            APIClientError: If the API request fails
        """
        params = {"fixture": fixture_id}
        return self._make_request("fixtures/events", params)
        
    def get_fixtures_statistics(self, fixture_id: str) -> Dict:
        """
        Get statistics for a specific fixture/match.
        
        Args:
            fixture_id: Fixture/match identifier
            
        Returns:
            Dict containing fixture statistics
            
        Raises:
            APIClientError: If the API request fails
        """
        params = {"fixture": fixture_id}
        return self._make_request("fixtures/statistics", params)
