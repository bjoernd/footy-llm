"""
Match tracker module for Football Match Notification Service.

This module provides functionality for discovering and tracking football matches
for configured teams. It handles:
- Discovering upcoming matches for teams of interest
- Tracking match status changes
- Determining when to start/stop polling for match updates
- Storing match information for later reference
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

from football_match_notification_service.api_client import FootballDataClient
from football_match_notification_service.config_manager import ConfigManager
from football_match_notification_service.logger import get_logger
from football_match_notification_service.models import Match, Team, MatchStatus
from football_match_notification_service.parsers import FootballDataParser

logger = get_logger(__name__)


class MatchTracker:
    """
    Tracks football matches for configured teams.
    """

    def __init__(
        self,
        api_client: FootballDataClient,
        config: ConfigManager,
        storage_path: Optional[str] = None,
    ):
        """
        Initialize the match tracker.

        Args:
            api_client: API client for fetching match data
            config: Configuration manager
            storage_path: Path to store match data (default: ~/.football_matches)
        """
        self.api_client = api_client
        self.config = config
        self.parser = FootballDataParser()

        # Set up storage path
        if storage_path is None:
            home_dir = os.path.expanduser("~")
            storage_path = os.path.join(home_dir, ".football_matches")

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize match storage
        self.upcoming_matches: Dict[str, Match] = {}
        self.active_matches: Dict[str, Match] = {}
        self.recent_matches: Dict[str, Match] = {}

        # Load stored matches
        self._load_matches()

        # Get team configuration
        self.teams_to_track = self._get_teams_to_track()
        self.team_ids = {team.id for team in self.teams_to_track}

        # Configuration for match discovery
        self.discovery_days = self.config.get("polling.discovery_days", 3)
        self.match_retention_days = self.config.get("polling.match_retention_days", 7)

        logger.info(f"Match tracker initialized with {len(self.teams_to_track)} teams")

    def _get_teams_to_track(self) -> List[Team]:
        """
        Get the list of teams to track from configuration.

        Returns:
            List of Team objects
        """
        teams_config = self.config.get("teams", [])
        teams = []

        for team_config in teams_config:
            team = Team(
                id=team_config.get("team_id"),
                name=team_config.get("name"),
                short_name=team_config.get("short_name", team_config.get("name")),
                country=team_config.get("country", ""),
            )
            teams.append(team)

        return teams

    def discover_matches(self) -> List[Match]:
        """
        Discover upcoming matches for tracked teams.

        Returns:
            List of newly discovered matches
        """
        logger.info("Discovering upcoming matches")

        # Calculate date range for discovery
        today = datetime.now().date()
        end_date = today + timedelta(days=self.discovery_days)

        # Fetch matches for each team
        new_matches = []

        for team in self.teams_to_track:
            try:
                # Get matches for this team
                response = self.api_client.get_team_matches(
                    team_id=team.id,
                    date_from=today.isoformat(),
                    date_to=end_date.isoformat(),
                )

                # Parse matches
                matches = self.parser.parse_matches(response)

                # Filter for matches not already tracked
                for match in matches:
                    match_id = match.id

                    if (
                        match_id not in self.upcoming_matches
                        and match_id not in self.active_matches
                        and match_id not in self.recent_matches
                    ):

                        self.upcoming_matches[match_id] = match
                        new_matches.append(match)
                        logger.info(
                            f"Discovered new match: {match.home_team.name} vs {match.away_team.name}"
                        )

            except Exception as e:
                logger.error(
                    f"Error discovering matches for team {team.name}: {str(e)}"
                )

        # Save updated matches
        self._save_matches()

        return new_matches

    def update_match_status(self, match_id: str) -> Tuple[Optional[Match], bool]:
        """
        Update the status of a specific match.

        Args:
            match_id: ID of the match to update

        Returns:
            Tuple of (updated match, status_changed)
        """
        # Find the match in our collections
        match = None
        if match_id in self.upcoming_matches:
            match = self.upcoming_matches[match_id]
        elif match_id in self.active_matches:
            match = self.active_matches[match_id]
        elif match_id in self.recent_matches:
            match = self.recent_matches[match_id]

        if not match:
            logger.warning(f"Attempted to update unknown match: {match_id}")
            return None, False

        try:
            # Fetch current match data
            response = self.api_client.get_match(match_id)
            updated_match = self.parser.parse_match(response)

            # Check if status changed
            status_changed = match.status != updated_match.status

            # Update match in appropriate collection based on status
            if updated_match.status == MatchStatus.FINISHED:
                # Move to recent matches if finished
                if match_id in self.upcoming_matches:
                    del self.upcoming_matches[match_id]
                if match_id in self.active_matches:
                    del self.active_matches[match_id]
                self.recent_matches[match_id] = updated_match

            elif updated_match.status in [
                MatchStatus.IN_PLAY,
                MatchStatus.PAUSED,
                MatchStatus.SUSPENDED,
            ]:
                # Move to active matches if in play
                if match_id in self.upcoming_matches:
                    del self.upcoming_matches[match_id]
                if match_id in self.recent_matches:
                    del self.recent_matches[match_id]
                self.active_matches[match_id] = updated_match

            else:
                # Keep in upcoming matches
                if match_id in self.active_matches:
                    del self.active_matches[match_id]
                if match_id in self.recent_matches:
                    del self.recent_matches[match_id]
                self.upcoming_matches[match_id] = updated_match

            # Save updated matches
            self._save_matches()

            if status_changed:
                logger.info(
                    f"Match status changed: {updated_match.home_team.name} vs {updated_match.away_team.name} - {updated_match.status}"
                )

            return updated_match, status_changed

        except Exception as e:
            logger.error(f"Error updating match {match_id}: {str(e)}")
            return match, False

    def get_matches_to_monitor(self) -> List[Match]:
        """
        Get matches that should be actively monitored.

        Returns:
            List of matches to monitor
        """
        # All active matches should be monitored
        matches_to_monitor = list(self.active_matches.values())

        # Add upcoming matches that are starting soon
        now = datetime.now()
        soon = now + timedelta(minutes=30)

        for match in self.upcoming_matches.values():
            if match.start_time and match.start_time <= soon:
                matches_to_monitor.append(match)

        return matches_to_monitor

    def clean_old_matches(self) -> int:
        """
        Remove old matches from storage.

        Returns:
            Number of matches removed
        """
        cutoff_date = datetime.now() - timedelta(days=self.match_retention_days)
        matches_to_remove = []

        for match_id, match in self.recent_matches.items():
            if match.start_time and match.start_time < cutoff_date:
                matches_to_remove.append(match_id)

        for match_id in matches_to_remove:
            del self.recent_matches[match_id]

        if matches_to_remove:
            self._save_matches()
            logger.info(f"Removed {len(matches_to_remove)} old matches from storage")

        return len(matches_to_remove)

    def _load_matches(self) -> None:
        """Load matches from storage files."""
        self._load_match_collection("upcoming_matches")
        self._load_match_collection("active_matches")
        self._load_match_collection("recent_matches")

    def _load_match_collection(self, collection_name: str) -> None:
        """
        Load a specific match collection from storage.

        Args:
            collection_name: Name of the collection to load
        """
        file_path = self.storage_path / f"{collection_name}.json"

        if not file_path.exists():
            return

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            matches = {}
            for match_data in data:
                match = Match.from_dict(match_data)
                matches[match.id] = match

            setattr(self, collection_name, matches)
            logger.debug(f"Loaded {len(matches)} matches from {collection_name}")

        except Exception as e:
            logger.error(f"Error loading {collection_name}: {str(e)}")

    def _save_matches(self) -> None:
        """Save all match collections to storage."""
        self._save_match_collection("upcoming_matches")
        self._save_match_collection("active_matches")
        self._save_match_collection("recent_matches")

    def _save_match_collection(self, collection_name: str) -> None:
        """
        Save a specific match collection to storage.

        Args:
            collection_name: Name of the collection to save
        """
        file_path = self.storage_path / f"{collection_name}.json"

        try:
            matches = getattr(self, collection_name)
            data = [match.to_dict() for match in matches.values()]

            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(data)} matches to {collection_name}")

        except Exception as e:
            logger.error(f"Error saving {collection_name}: {str(e)}")

    def get_match(self, match_id: str) -> Optional[Match]:
        """
        Get a match by ID.

        Args:
            match_id: ID of the match to get

        Returns:
            Match if found, None otherwise
        """
        if match_id in self.upcoming_matches:
            return self.upcoming_matches[match_id]
        elif match_id in self.active_matches:
            return self.active_matches[match_id]
        elif match_id in self.recent_matches:
            return self.recent_matches[match_id]
        return None

    def get_all_matches(self) -> Dict[str, List[Match]]:
        """
        Get all tracked matches organized by status.

        Returns:
            Dictionary with upcoming, active, and recent matches
        """
        return {
            "upcoming": list(self.upcoming_matches.values()),
            "active": list(self.active_matches.values()),
            "recent": list(self.recent_matches.values()),
        }


# Singleton instance
_match_tracker_instance: Optional[MatchTracker] = None


def get_match_tracker(
    api_client: Optional[FootballDataClient] = None,
    config: Optional[ConfigManager] = None,
    storage_path: Optional[str] = None,
) -> MatchTracker:
    """
    Get the singleton match tracker instance.

    Args:
        api_client: API client for fetching match data
        config: Configuration manager
        storage_path: Path to store match data

    Returns:
        The match tracker instance
    """
    global _match_tracker_instance

    if _match_tracker_instance is None:
        from football_match_notification_service.config_manager import (
            get_config_manager,
        )

        if api_client is None:
            from football_match_notification_service.api_client import (
                get_football_data_client,
            )

            api_client = get_football_data_client()

        if config is None:
            config = get_config_manager()

        _match_tracker_instance = MatchTracker(
            api_client=api_client,
            config=config,
            storage_path=storage_path,
        )

    return _match_tracker_instance
