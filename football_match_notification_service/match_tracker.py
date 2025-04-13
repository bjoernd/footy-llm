"""
Match tracker module for Football Match Notification Service.

This module provides functionality for discovering and tracking football matches
for configured teams. It handles:
- Discovering upcoming matches for teams of interest
- Tracking match status changes
- Determining when to start/stop polling for a match
- Storing match information for later reference
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

from football_match_notification_service.api_client import APIFootballClient
from football_match_notification_service.config_manager import ConfigManager
from football_match_notification_service.logger import get_logger
from football_match_notification_service.models import Match, Team, MatchStatus, Score
from football_match_notification_service.parsers import APIFootballParser

logger = get_logger(__name__)


class MatchTracker:
    """
    Tracks football matches for configured teams.
    """

    def __init__(
        self,
        api_client: APIFootballClient,
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
        self.parser = APIFootballParser()
        
        # Set up storage path
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path.home() / ".football_matches"
            
        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize match storage
        self.matches: Dict[str, Match] = {}
        self.load_matches()

    def discover_matches(self, days_ahead: Optional[int] = None) -> List[Match]:
        """
        Discover upcoming matches for configured teams.

        Args:
            days_ahead: Number of days ahead to look for matches (default: from config)

        Returns:
            List of discovered matches
        """
        if days_ahead is None:
            days_ahead = self.config.get_with_default("polling_settings.match_discovery_days") or 3
            
        logger.info(f"Discovering matches for the next {days_ahead} days")
        
        # Get configured teams
        teams = self.config.get("teams", [])
        if not teams:
            logger.warning("No teams configured for match discovery")
            return []
            
        # Calculate date range
        today = datetime.now().date()
        end_date = today + timedelta(days=days_ahead)
        
        today_str = today.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        discovered_matches = []
        
        # Fetch matches for each team
        for team_config in teams:
            team_id = team_config.get("team_id")
            team_name = team_config.get("name")
            
            if not team_id:
                logger.warning(f"Missing team_id for team: {team_name}")
                continue
                
            logger.info(f"Fetching matches for team: {team_name} (ID: {team_id})")
            
            try:
                # Get matches for this team
                response = self.api_client.get_matches_by_team(
                    team_id=team_id,
                    from_date=today_str,
                    to_date=end_date_str,
                )
                
                # Parse matches
                matches = self.parser.parse_matches(response)
                
                # Add to discovered matches
                for match in matches:
                    # Check if we already know about this match
                    if match.id in self.matches:
                        # Update existing match with new data
                        self.matches[match.id] = match
                        logger.debug(f"Updated existing match: {match.home_team.name} vs {match.away_team.name}")
                    else:
                        # Add new match
                        self.matches[match.id] = match
                        discovered_matches.append(match)
                        logger.info(f"Discovered new match: {match.home_team.name} vs {match.away_team.name} on {match.start_time}")
                
            except Exception as e:
                logger.error(f"Error discovering matches for team {team_name}: {e}")
                
        # Save updated matches
        self.save_matches()
        
        return discovered_matches

    def get_match(self, match_id: str) -> Optional[Match]:
        """
        Get a match by ID.

        Args:
            match_id: Match ID

        Returns:
            Match if found, None otherwise
        """
        return self.matches.get(match_id)

    def get_matches_by_status(self, status: MatchStatus) -> List[Match]:
        """
        Get matches with a specific status.

        Args:
            status: Match status to filter by

        Returns:
            List of matches with the specified status
        """
        return [match for match in self.matches.values() if match.status == status]

    def get_active_matches(self) -> List[Match]:
        """
        Get all active matches (in-play or half-time).

        Returns:
            List of active matches
        """
        active_statuses = [MatchStatus.IN_PLAY, MatchStatus.HALF_TIME, MatchStatus.PAUSED]
        return [match for match in self.matches.values() if match.status in active_statuses]

    def get_upcoming_matches(self, hours: int = 24) -> List[Match]:
        """
        Get upcoming matches within the specified time window.

        Args:
            hours: Number of hours to look ahead

        Returns:
            List of upcoming matches
        """
        now = datetime.now()
        cutoff = now + timedelta(hours=hours)
        
        upcoming_statuses = [MatchStatus.SCHEDULED, MatchStatus.TIMED]
        
        return [
            match for match in self.matches.values()
            if match.status in upcoming_statuses and now <= match.start_time <= cutoff
        ]

    def update_match_status(self, match_id: str) -> Optional[Match]:
        """
        Update the status of a specific match.

        Args:
            match_id: Match ID

        Returns:
            Updated match if successful, None otherwise
        """
        if match_id not in self.matches:
            logger.warning(f"Cannot update unknown match: {match_id}")
            return None
            
        try:
            # Get latest match data
            response = self.api_client.get_match_details(match_id)
            
            # Parse match data
            matches = self.parser.parse_matches(response)
            
            if not matches:
                logger.warning(f"No match data returned for ID: {match_id}")
                return None
                
            # Update match in storage
            updated_match = matches[0]
            old_match = self.matches[match_id]
            
            # Check if status has changed
            if old_match.status != updated_match.status:
                logger.info(
                    f"Match status changed: {old_match.home_team.name} vs {old_match.away_team.name} "
                    f"from {old_match.status.value} to {updated_match.status.value}"
                )
                
            # Check if score has changed
            if old_match.score.home != updated_match.score.home or old_match.score.away != updated_match.score.away:
                logger.info(
                    f"Score changed: {old_match.home_team.name} vs {old_match.away_team.name} "
                    f"from {old_match.score.home}-{old_match.score.away} to "
                    f"{updated_match.score.home}-{updated_match.score.away}"
                )
                
            # Update match
            self.matches[match_id] = updated_match
            self.save_matches()
            
            return updated_match
            
        except Exception as e:
            logger.error(f"Error updating match {match_id}: {e}")
            return None

    def update_active_matches(self) -> List[Match]:
        """
        Update all active matches.

        Returns:
            List of updated matches
        """
        active_matches = self.get_active_matches()
        
        if not active_matches:
            logger.debug("No active matches to update")
            return []
            
        logger.info(f"Updating {len(active_matches)} active matches")
        
        updated_matches = []
        
        for match in active_matches:
            updated_match = self.update_match_status(match.id)
            if updated_match:
                updated_matches.append(updated_match)
                
        return updated_matches

    def clean_old_matches(self, days: Optional[int] = None) -> int:
        """
        Remove old matches from storage.

        Args:
            days: Number of days to keep matches for (default: from config)

        Returns:
            Number of matches removed
        """
        if days is None:
            days = self.config.get_with_default("polling_settings.match_history_days") or 7
            
        cutoff = datetime.now() - timedelta(days=days)
        
        old_matches = [
            match_id for match_id, match in self.matches.items()
            if match.start_time < cutoff and match.status in [MatchStatus.FINISHED, MatchStatus.CANCELLED, MatchStatus.POSTPONED]
        ]
        
        if not old_matches:
            logger.debug(f"No matches older than {days} days to clean up")
            return 0
            
        logger.info(f"Cleaning up {len(old_matches)} matches older than {days} days")
        
        for match_id in old_matches:
            del self.matches[match_id]
            
        self.save_matches()
        
        return len(old_matches)

    def save_matches(self) -> None:
        """
        Save matches to storage.
        """
        matches_file = self.storage_path / "matches.json"
        
        # Convert matches to serializable format
        serialized_matches = {}
        for match_id, match in self.matches.items():
            serialized_matches[match_id] = {
                "id": match.id,
                "home_team": {
                    "id": match.home_team.id,
                    "name": match.home_team.name,
                    "short_name": match.home_team.short_name,
                    "logo_url": match.home_team.logo_url,
                    "country": match.home_team.country,
                },
                "away_team": {
                    "id": match.away_team.id,
                    "name": match.away_team.name,
                    "short_name": match.away_team.short_name,
                    "logo_url": match.away_team.logo_url,
                    "country": match.away_team.country,
                },
                "start_time": match.start_time.isoformat(),
                "status": match.status.value,
                "score": {
                    "home": match.score.home,
                    "away": match.score.away,
                },
                "competition": match.competition,
                "venue": match.venue,
                "referee": match.referee,
                "round": match.round,
                "season": match.season,
            }
            
        try:
            with open(matches_file, "w") as f:
                json.dump(serialized_matches, f, indent=2)
                
            logger.debug(f"Saved {len(self.matches)} matches to {matches_file}")
        except Exception as e:
            logger.error(f"Error saving matches to {matches_file}: {e}")

    def load_matches(self) -> None:
        """
        Load matches from storage.
        """
        matches_file = self.storage_path / "matches.json"
        
        if not matches_file.exists():
            logger.debug(f"No matches file found at {matches_file}")
            return
            
        try:
            with open(matches_file, "r") as f:
                serialized_matches = json.load(f)
                
            # Convert serialized matches back to Match objects
            for match_id, match_data in serialized_matches.items():
                home_team = Team(
                    id=match_data["home_team"]["id"],
                    name=match_data["home_team"]["name"],
                    short_name=match_data["home_team"].get("short_name"),
                    logo_url=match_data["home_team"].get("logo_url"),
                    country=match_data["home_team"].get("country"),
                )
                
                away_team = Team(
                    id=match_data["away_team"]["id"],
                    name=match_data["away_team"]["name"],
                    short_name=match_data["away_team"].get("short_name"),
                    logo_url=match_data["away_team"].get("logo_url"),
                    country=match_data["away_team"].get("country"),
                )
                
                start_time = datetime.fromisoformat(match_data["start_time"])
                status = MatchStatus(match_data["status"])
                score = Score(home=match_data["score"]["home"], away=match_data["score"]["away"])
                
                match = Match(
                    id=match_data["id"],
                    home_team=home_team,
                    away_team=away_team,
                    start_time=start_time,
                    status=status,
                    score=score,
                    competition=match_data.get("competition"),
                    venue=match_data.get("venue"),
                    referee=match_data.get("referee"),
                    round=match_data.get("round"),
                    season=match_data.get("season"),
                )
                
                self.matches[match_id] = match
                
            logger.info(f"Loaded {len(self.matches)} matches from {matches_file}")
        except Exception as e:
            logger.error(f"Error loading matches from {matches_file}: {e}")
            # Initialize with empty dict if loading fails
            self.matches = {}
