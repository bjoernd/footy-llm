"""
API Client module for Football Match Notification Service.

This module provides an abstract base class for API clients and a concrete implementation
for the Football-Data.org API.
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
        self.base_url = self._get_base_url()
        self.timeout = self._get_timeout()

    @abc.abstractmethod
    def _get_base_url(self) -> str:
        """
        Get the base URL for API requests.

        Returns:
            str: Base URL for the API
        """
        pass

    @abc.abstractmethod
    def _get_timeout(self) -> int:
        """
        Get the timeout for API requests.

        Returns:
            int: Timeout in seconds
        """
        pass

    @abc.abstractmethod
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for API requests.

        Returns:
            Dict[str, str]: Headers for API requests
        """
        pass

    @abc.abstractmethod
    def get_matches(self, team_id: Optional[str] = None, date_from: Optional[str] = None,
                   date_to: Optional[str] = None) -> Dict[str, Any]:
        """
        Get matches for a team within a date range.

        Args:
            team_id: Optional team ID to filter matches
            date_from: Optional start date in ISO format (YYYY-MM-DD)
            date_to: Optional end date in ISO format (YYYY-MM-DD)

        Returns:
            Dict[str, Any]: Match data
        """
        pass

    @abc.abstractmethod
    def get_match_details(self, match_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific match.

        Args:
            match_id: Match ID

        Returns:
            Dict[str, Any]: Match details
        """
        pass

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make an API request.

        Args:
            endpoint: API endpoint
            params: Optional query parameters

        Returns:
            Dict[str, Any]: API response data

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit is exceeded
            APIClientError: For other API errors
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        try:
            logger.debug(f"Making API request to {url}")
            response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            
            # Handle HTTP errors
            if response.status_code == 401:
                raise AuthenticationError(f"Authentication failed: {response.text}")
            elif response.status_code == 429:
                raise RateLimitError(f"Rate limit exceeded: {response.text}")
            elif response.status_code >= 400:
                raise APIClientError(f"API error {response.status_code}: {response.text}")
            
            # Parse JSON response
            try:
                return response.json()
            except json.JSONDecodeError:
                raise APIClientError(f"Invalid JSON response: {response.text}")
                
        except requests.RequestException as e:
            raise APIClientError(f"Request failed: {str(e)}")


class FootballDataClient(APIClient):
    """Client for the Football-Data.org API."""

    def _get_base_url(self) -> str:
        """
        Get the base URL for Football-Data.org API.

        Returns:
            str: Base URL for the API
        """
        return self.config_manager.get("api.football_data.base_url", "https://api.football-data.org/v4")

    def _get_timeout(self) -> int:
        """
        Get the timeout for API requests.

        Returns:
            int: Timeout in seconds
        """
        return self.config_manager.get("api.football_data.timeout", 30)

    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for Football-Data.org API requests.

        Returns:
            Dict[str, str]: Headers for API requests
        """
        api_key = self.config_manager.get("api.football_data.api_key")
        if not api_key:
            raise AuthenticationError("API key not found in configuration")
        
        return {
            "X-Auth-Token": api_key,
            "Accept": "application/json"
        }

    def get_matches(self, team_id: Optional[str] = None, date_from: Optional[str] = None,
                   date_to: Optional[str] = None) -> Dict[str, Any]:
        """
        Get matches for a team within a date range.

        Args:
            team_id: Optional team ID to filter matches
            date_from: Optional start date in ISO format (YYYY-MM-DD)
            date_to: Optional end date in ISO format (YYYY-MM-DD)

        Returns:
            Dict[str, Any]: Match data
        """
        params = {}
        
        if team_id:
            params["team"] = team_id
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
            
        return self._make_request("/matches", params)

    def get_match_details(self, match_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific match.

        Args:
            match_id: Match ID

        Returns:
            Dict[str, Any]: Match details
        """
        return self._make_request(f"/matches/{match_id}")
