"""
Data models for Football Match Notification Service.

This module provides data models for teams, matches, and events.
"""

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Union


class MatchStatus(Enum):
    """Enum for match status."""

    SCHEDULED = "SCHEDULED"  # Match is scheduled but not started
    TIMED = "TIMED"  # Match is scheduled with a confirmed time
    IN_PLAY = "IN_PLAY"  # Match is currently in play
    PAUSED = "PAUSED"  # Match is paused (e.g., during half-time)
    HALF_TIME = "HALF_TIME"  # Half-time break
    FINISHED = "FINISHED"  # Match has finished
    SUSPENDED = "SUSPENDED"  # Match has been suspended
    POSTPONED = "POSTPONED"  # Match has been postponed
    CANCELLED = "CANCELLED"  # Match has been cancelled
    AWARDED = "AWARDED"  # Match result has been awarded (e.g., forfeit)
    UNKNOWN = "UNKNOWN"  # Status is unknown

    @classmethod
    def from_api_football(cls, status: str) -> 'MatchStatus':
        """
        Convert API-Football status to MatchStatus.
        
        Args:
            status: Status string from API-Football
            
        Returns:
            Corresponding MatchStatus enum value
        """
        status_map = {
            "TBD": cls.SCHEDULED,
            "NS": cls.SCHEDULED,  # Not Started
            "1H": cls.IN_PLAY,    # First Half
            "HT": cls.HALF_TIME,  # Half Time
            "2H": cls.IN_PLAY,    # Second Half
            "ET": cls.IN_PLAY,    # Extra Time
            "BT": cls.IN_PLAY,    # Break Time
            "P": cls.IN_PLAY,     # Penalty In Progress
            "SUSP": cls.SUSPENDED,  # Match Suspended
            "INT": cls.PAUSED,    # Match Interrupted
            "FT": cls.FINISHED,   # Match Finished
            "AET": cls.FINISHED,  # Match Finished After Extra Time
            "PEN": cls.FINISHED,  # Match Finished After Penalties
            "PST": cls.POSTPONED, # Match Postponed
            "CANC": cls.CANCELLED, # Match Cancelled
            "ABD": cls.CANCELLED, # Match Abandoned
            "AWD": cls.AWARDED,   # Technical Loss
            "WO": cls.AWARDED,    # WalkOver
        }
        
        return status_map.get(status, cls.UNKNOWN)


class EventType(Enum):
    """Enum for event types."""

    GOAL = "GOAL"
    YELLOW_CARD = "YELLOW_CARD"
    RED_CARD = "RED_CARD"
    SUBSTITUTION = "SUBSTITUTION"
    PENALTY_MISSED = "PENALTY_MISSED"
    PENALTY_SCORED = "PENALTY_SCORED"
    MATCH_START = "MATCH_START"
    MATCH_END = "MATCH_END"
    HALF_TIME = "HALF_TIME"
    EXTRA_TIME = "EXTRA_TIME"
    PENALTIES = "PENALTIES"
    OTHER = "OTHER"
    
    @classmethod
    def from_api_football(cls, event_type: str) -> 'EventType':
        """
        Convert API-Football event type to EventType.
        
        Args:
            event_type: Event type string from API-Football
            
        Returns:
            Corresponding EventType enum value
        """
        event_map = {
            "Goal": cls.GOAL,
            "Card": cls.YELLOW_CARD,  # Will be refined based on card color
            "Subst": cls.SUBSTITUTION,
            "Var": cls.OTHER,
            "Penalty missed": cls.PENALTY_MISSED,
        }
        
        return event_map.get(event_type, cls.OTHER)


@dataclass
class Team:
    """Team data model."""

    id: str
    name: str
    short_name: Optional[str] = None
    logo_url: Optional[str] = None
    country: Optional[str] = None
    
    @classmethod
    def from_api_football(cls, team_data: Dict) -> 'Team':
        """
        Create a Team instance from API-Football team data.
        
        Args:
            team_data: Team data from API-Football
            
        Returns:
            Team instance
        """
        return cls(
            id=str(team_data.get("id", "")),
            name=team_data.get("name", ""),
            short_name=team_data.get("code", None),
            logo_url=team_data.get("logo", None),
            country=team_data.get("country", None),
        )


@dataclass
class Score:
    """Score data model."""

    home: int
    away: int
    
    @classmethod
    def from_api_football(cls, score_data: Dict) -> 'Score':
        """
        Create a Score instance from API-Football score data.
        
        Args:
            score_data: Score data from API-Football
            
        Returns:
            Score instance
        """
        return cls(
            home=int(score_data.get("home", 0) or 0),
            away=int(score_data.get("away", 0) or 0),
        )


@dataclass
class Match:
    """Match data model."""

    id: str
    home_team: Team
    away_team: Team
    start_time: datetime.datetime
    status: MatchStatus
    score: Score
    competition: Optional[str] = None
    venue: Optional[str] = None
    referee: Optional[str] = None
    round: Optional[str] = None
    season: Optional[str] = None
    
    @classmethod
    def from_api_football(cls, match_data: Dict) -> 'Match':
        """
        Create a Match instance from API-Football match data.
        
        Args:
            match_data: Match data from API-Football
            
        Returns:
            Match instance
        """
        fixture = match_data.get("fixture", {})
        teams = match_data.get("teams", {})
        goals = match_data.get("goals", {})
        league = match_data.get("league", {})
        
        # Parse start time
        start_time_str = fixture.get("date", "")
        try:
            start_time = datetime.datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            start_time = datetime.datetime.now()
        
        return cls(
            id=str(fixture.get("id", "")),
            home_team=Team.from_api_football(teams.get("home", {})),
            away_team=Team.from_api_football(teams.get("away", {})),
            start_time=start_time,
            status=MatchStatus.from_api_football(fixture.get("status", {}).get("short", "")),
            score=Score.from_api_football(goals),
            competition=league.get("name"),
            venue=fixture.get("venue", {}).get("name"),
            referee=fixture.get("referee"),
            round=league.get("round"),
            season=str(league.get("season")) if league.get("season") is not None else None,
        )


@dataclass
class Event:
    """Event data model."""

    id: str
    match_id: str
    type: EventType
    minute: Optional[int] = None
    team_id: Optional[str] = None
    player_name: Optional[str] = None
    description: Optional[str] = None
    score_home: Optional[int] = None
    score_away: Optional[int] = None
    
    @classmethod
    def from_api_football(cls, event_data: Dict, match_id: str) -> 'Event':
        """
        Create an Event instance from API-Football event data.
        
        Args:
            event_data: Event data from API-Football
            match_id: ID of the match this event belongs to
            
        Returns:
            Event instance
        """
        event_type = EventType.from_api_football(event_data.get("type", ""))
        
        # Refine card type based on detail
        if event_type == EventType.YELLOW_CARD and event_data.get("detail") == "Red Card":
            event_type = EventType.RED_CARD
            
        # Create description
        description_parts = []
        if event_data.get("player", {}).get("name"):
            description_parts.append(event_data["player"]["name"])
        if event_data.get("detail"):
            description_parts.append(event_data["detail"])
        if event_data.get("comments"):
            description_parts.append(event_data["comments"])
            
        description = " - ".join(filter(None, description_parts)) if description_parts else None
        
        # Extract team ID
        team_id = None
        if event_data.get("team", {}).get("id"):
            team_id = str(event_data["team"]["id"])
            
        return cls(
            id=f"{match_id}_{event_data.get('time', {}).get('elapsed', 0)}_{event_type.value}_{team_id or ''}",
            match_id=match_id,
            type=event_type,
            minute=event_data.get("time", {}).get("elapsed"),
            team_id=team_id,
            player_name=event_data.get("player", {}).get("name"),
            description=description,
        )
        
    @classmethod
    def create_match_start_event(cls, match: Match) -> 'Event':
        """
        Create a match start event.
        
        Args:
            match: Match that has started
            
        Returns:
            Event instance for match start
        """
        return cls(
            id=f"{match.id}_START",
            match_id=match.id,
            type=EventType.MATCH_START,
            minute=0,
            description=f"Match started: {match.home_team.name} vs {match.away_team.name}",
            score_home=0,
            score_away=0,
        )
        
    @classmethod
    def create_match_end_event(cls, match: Match) -> 'Event':
        """
        Create a match end event.
        
        Args:
            match: Match that has ended
            
        Returns:
            Event instance for match end
        """
        return cls(
            id=f"{match.id}_END",
            match_id=match.id,
            type=EventType.MATCH_END,
            minute=90,  # Approximate, could be more with extra time
            description=f"Match ended: {match.home_team.name} {match.score.home}-{match.score.away} {match.away_team.name}",
            score_home=match.score.home,
            score_away=match.score.away,
        )
        
    @classmethod
    def create_half_time_event(cls, match: Match) -> 'Event':
        """
        Create a half-time event.
        
        Args:
            match: Match at half-time
            
        Returns:
            Event instance for half-time
        """
        return cls(
            id=f"{match.id}_HALF_TIME",
            match_id=match.id,
            type=EventType.HALF_TIME,
            minute=45,
            description=f"Half-time: {match.home_team.name} {match.score.home}-{match.score.away} {match.away_team.name}",
            score_home=match.score.home,
            score_away=match.score.away,
        )
