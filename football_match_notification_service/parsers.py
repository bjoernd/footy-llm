"""
Data parsers for Football Match Notification Service.

This module provides parsers for converting API responses to data models.
"""

import datetime
import uuid
from typing import Any, Dict, List, Optional

from football_match_notification_service.logger import get_logger
from football_match_notification_service.models import Event, EventType, Match, MatchStatus, Score, Team

# Set up logger
logger = get_logger(__name__)


class ParserError(Exception):
    """Exception raised for parsing errors."""
    pass


class FootballDataParser:
    """Parser for Football-Data.org API responses."""
    
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
            return Team(
                id=str(team_data["id"]),
                name=team_data["name"],
                short_name=team_data.get("shortName", team_data.get("tla")),
                logo_url=team_data.get("crest"),
                country=team_data.get("area", {}).get("name"),
            )
        except (KeyError, TypeError) as e:
            logger.error(f"Error parsing team data: {e}")
            raise ParserError(f"Error parsing team data: {e}")
    
    @staticmethod
    def parse_score(score_data: Dict[str, Any]) -> Score:
        """
        Parse score data from API response.
        
        Args:
            score_data: Score data from API
            
        Returns:
            Score: Parsed score object
            
        Raises:
            ParserError: If score data is invalid
        """
        try:
            # Try to get full time score first
            if "fullTime" in score_data:
                home = score_data["fullTime"].get("home", 0)
                away = score_data["fullTime"].get("away", 0)
            # Fall back to regular score
            else:
                home = score_data.get("home", 0)
                away = score_data.get("away", 0)
                
            # Handle None values
            if home is None:
                home = 0
            if away is None:
                away = 0
                
            return Score(home=home, away=away)
        except (KeyError, TypeError) as e:
            logger.error(f"Error parsing score data: {e}")
            return Score(0, 0)  # Default to 0-0 on error
    
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
            # Parse teams
            home_team = FootballDataParser.parse_team(match_data["homeTeam"])
            away_team = FootballDataParser.parse_team(match_data["awayTeam"])
            
            # Parse start time
            start_time_str = match_data["utcDate"]
            start_time = datetime.datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
            
            # Parse status
            status_str = match_data["status"]
            try:
                status = MatchStatus(status_str)
            except ValueError:
                status = MatchStatus.UNKNOWN
                logger.warning(f"Unknown match status: {status_str}")
            
            # Parse score
            score = FootballDataParser.parse_score(match_data.get("score", {}))
            
            # Parse competition
            competition = match_data.get("competition", {}).get("name")
            
            # Parse matchday
            matchday = match_data.get("matchday")
            
            # Create match object
            return Match(
                id=str(match_data["id"]),
                home_team=home_team,
                away_team=away_team,
                start_time=start_time,
                status=status,
                score=score,
                competition=competition,
                matchday=matchday,
                last_updated=datetime.datetime.now(),
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"Error parsing match data: {e}")
            raise ParserError(f"Error parsing match data: {e}")
    
    @staticmethod
    def parse_matches(matches_data: Dict[str, Any]) -> List[Match]:
        """
        Parse multiple matches from API response.
        
        Args:
            matches_data: Matches data from API
            
        Returns:
            List[Match]: List of parsed match objects
        """
        matches = []
        
        # Check if response has a 'matches' key
        if "matches" in matches_data:
            match_list = matches_data["matches"]
        else:
            match_list = matches_data
            
        if not isinstance(match_list, list):
            logger.error(f"Expected list of matches, got {type(match_list)}")
            return []
            
        for match_data in match_list:
            try:
                match = FootballDataParser.parse_match(match_data)
                matches.append(match)
            except ParserError as e:
                logger.error(f"Skipping match due to parsing error: {e}")
                continue
                
        return matches
    
    @staticmethod
    def extract_events(current_match: Match, previous_match: Optional[Match] = None) -> List[Event]:
        """
        Extract events by comparing current and previous match states.
        
        Args:
            current_match: Current match state
            previous_match: Previous match state (optional)
            
        Returns:
            List[Event]: List of detected events
        """
        events = []
        
        # If no previous match, check if match just started
        if previous_match is None:
            if current_match.is_live():
                # Match just started
                events.append(Event(
                    id=str(uuid.uuid4()),
                    match_id=current_match.id,
                    type=EventType.MATCH_START,
                    description=f"Match started: {current_match.home_team.name} vs {current_match.away_team.name}",
                ))
            return events
            
        # Check for status changes
        if previous_match.status != current_match.status:
            if current_match.is_live() and not previous_match.is_live():
                # Match started
                events.append(Event(
                    id=str(uuid.uuid4()),
                    match_id=current_match.id,
                    type=EventType.MATCH_START,
                    description=f"Match started: {current_match.home_team.name} vs {current_match.away_team.name}",
                ))
            elif current_match.is_finished() and not previous_match.is_finished():
                # Match ended
                events.append(Event(
                    id=str(uuid.uuid4()),
                    match_id=current_match.id,
                    type=EventType.MATCH_END,
                    description=f"Match ended: {current_match.home_team.name} {current_match.score} {current_match.away_team.name}",
                ))
                
        # Check for score changes
        if current_match.score.home > previous_match.score.home:
            # Home team scored
            events.append(Event(
                id=str(uuid.uuid4()),
                match_id=current_match.id,
                type=EventType.GOAL,
                team_id=current_match.home_team.id,
                description=f"GOAL! {current_match.home_team.name} {current_match.score}",
            ))
        elif current_match.score.away > previous_match.score.away:
            # Away team scored
            events.append(Event(
                id=str(uuid.uuid4()),
                match_id=current_match.id,
                type=EventType.GOAL,
                team_id=current_match.away_team.id,
                description=f"GOAL! {current_match.away_team.name} {current_match.score}",
            ))
            
        return events
