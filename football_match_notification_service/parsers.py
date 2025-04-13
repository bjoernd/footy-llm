"""
Data parsers for Football Match Notification Service.

This module provides parsers for converting API responses to data models.
"""

import datetime
import uuid
from typing import Any, Dict, List, Optional

from football_match_notification_service.logger import get_logger
from football_match_notification_service.models import (
    Event,
    EventType,
    Match,
    MatchStatus,
    Score,
    Team,
)

# Set up logger
logger = get_logger(__name__)


class ParserError(Exception):
    """Exception raised for parsing errors."""

    pass


class APIFootballParser:
    """Parser for API-Football.com API responses."""

    @staticmethod
    def parse_team(team_data: Dict[str, Any]) -> Team:
        """
        Parse team data from API response.

        Args:
            team_data: Team data from API

        Returns:
            Team: Parsed team object

        Raises:
            ParserError: If required fields are missing
        """
        try:
            return Team.from_api_football(team_data)
        except Exception as e:
            logger.error(f"Error parsing team data: {e}", extra={"team_data": team_data})
            raise ParserError(f"Failed to parse team data: {e}") from e

    @staticmethod
    def parse_match(match_data: Dict[str, Any]) -> Match:
        """
        Parse match data from API response.

        Args:
            match_data: Match data from API

        Returns:
            Match: Parsed match object

        Raises:
            ParserError: If required fields are missing
        """
        try:
            return Match.from_api_football(match_data)
        except Exception as e:
            logger.error(f"Error parsing match data: {e}", extra={"match_data": match_data})
            raise ParserError(f"Failed to parse match data: {e}") from e

    @staticmethod
    def parse_matches(response_data: Dict[str, Any]) -> List[Match]:
        """
        Parse multiple matches from API response.

        Args:
            response_data: API response containing matches

        Returns:
            List[Match]: List of parsed match objects

        Raises:
            ParserError: If the response format is invalid
        """
        try:
            matches = []
            response = response_data.get("response", [])
            
            if not isinstance(response, list):
                raise ParserError("Invalid response format: 'response' is not a list")
                
            for match_data in response:
                try:
                    match = APIFootballParser.parse_match(match_data)
                    matches.append(match)
                except Exception as e:
                    logger.warning(f"Skipping invalid match data: {e}")
                    continue
                    
            return matches
        except Exception as e:
            logger.error(f"Error parsing matches: {e}", extra={"response_data": response_data})
            raise ParserError(f"Failed to parse matches: {e}") from e

    @staticmethod
    def parse_event(event_data: Dict[str, Any], match_id: str) -> Event:
        """
        Parse event data from API response.

        Args:
            event_data: Event data from API
            match_id: ID of the match this event belongs to

        Returns:
            Event: Parsed event object

        Raises:
            ParserError: If required fields are missing
        """
        try:
            return Event.from_api_football(event_data, match_id)
        except Exception as e:
            logger.error(f"Error parsing event data: {e}", extra={"event_data": event_data})
            raise ParserError(f"Failed to parse event data: {e}") from e

    @staticmethod
    def parse_events(response_data: Dict[str, Any], match_id: str) -> List[Event]:
        """
        Parse multiple events from API response.

        Args:
            response_data: API response containing events
            match_id: ID of the match these events belong to

        Returns:
            List[Event]: List of parsed event objects

        Raises:
            ParserError: If the response format is invalid
        """
        try:
            events = []
            response = response_data.get("response", [])
            
            if not isinstance(response, list):
                raise ParserError("Invalid response format: 'response' is not a list")
                
            for event_data in response:
                try:
                    event = APIFootballParser.parse_event(event_data, match_id)
                    events.append(event)
                except Exception as e:
                    logger.warning(f"Skipping invalid event data: {e}")
                    continue
                    
            return events
        except Exception as e:
            logger.error(f"Error parsing events: {e}", extra={"response_data": response_data})
            raise ParserError(f"Failed to parse events: {e}") from e

    @staticmethod
    def normalize_date(date_str: str) -> str:
        """
        Normalize date string to YYYY-MM-DD format.

        Args:
            date_str: Date string in various formats

        Returns:
            Normalized date string in YYYY-MM-DD format

        Raises:
            ValueError: If the date string cannot be parsed
        """
        try:
            # Try ISO format first
            date = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return date.strftime("%Y-%m-%d")
        except ValueError:
            # Try YYYY-MM-DD format
            if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
                return date_str
                
            # For ambiguous formats like DD/MM/YYYY or MM/DD/YYYY, we'll assume DD/MM/YYYY
            # as it's more common in international football
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:
                    day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                    # If day is > 12, it must be DD/MM format
                    if day > 12:
                        return f"{year}-{month:02d}-{day:02d}"
                    # Otherwise, assume DD/MM format (international standard)
                    return f"{year}-{month:02d}-{day:02d}"
                    
            # Try other formats as a fallback
            for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
                try:
                    date = datetime.datetime.strptime(date_str, fmt)
                    return date.strftime("%Y-%m-%d")
                except ValueError:
                    continue
                    
            raise ValueError(f"Could not parse date string: {date_str}")

    @staticmethod
    def extract_team_ids(response_data: Dict[str, Any]) -> List[str]:
        """
        Extract team IDs from API response.

        Args:
            response_data: API response containing teams

        Returns:
            List[str]: List of team IDs

        Raises:
            ParserError: If the response format is invalid
        """
        try:
            team_ids = []
            response = response_data.get("response", [])
            
            if not isinstance(response, list):
                raise ParserError("Invalid response format: 'response' is not a list")
                
            for team_data in response:
                team = team_data.get("team", {})
                if team and "id" in team:
                    team_ids.append(str(team["id"]))
                    
            return team_ids
        except Exception as e:
            logger.error(f"Error extracting team IDs: {e}", extra={"response_data": response_data})
            raise ParserError(f"Failed to extract team IDs: {e}") from e
