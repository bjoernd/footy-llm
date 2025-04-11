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
    SCHEDULED = "SCHEDULED"
    TIMED = "TIMED"
    IN_PLAY = "IN_PLAY"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"
    SUSPENDED = "SUSPENDED"
    POSTPONED = "POSTPONED"
    CANCELLED = "CANCELLED"
    AWARDED = "AWARDED"
    UNKNOWN = "UNKNOWN"


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


@dataclass
class Team:
    """Team data model."""
    id: str
    name: str
    short_name: Optional[str] = None
    logo_url: Optional[str] = None
    country: Optional[str] = None
    
    def __post_init__(self):
        """Validate and normalize team data."""
        if not self.id:
            raise ValueError("Team ID is required")
        if not self.name:
            raise ValueError("Team name is required")
        if not self.short_name:
            self.short_name = self.name


@dataclass
class Score:
    """Score data model."""
    home: int = 0
    away: int = 0
    
    def __str__(self) -> str:
        """String representation of score."""
        return f"{self.home}-{self.away}"


@dataclass
class Match:
    """Match data model."""
    id: str
    home_team: Team
    away_team: Team
    start_time: datetime.datetime
    status: MatchStatus = MatchStatus.SCHEDULED
    score: Score = field(default_factory=Score)
    competition: Optional[str] = None
    matchday: Optional[int] = None
    last_updated: Optional[datetime.datetime] = None
    events: List["Event"] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate and normalize match data."""
        if not self.id:
            raise ValueError("Match ID is required")
        if not isinstance(self.home_team, Team):
            raise ValueError("Home team must be a Team object")
        if not isinstance(self.away_team, Team):
            raise ValueError("Away team must be a Team object")
        if not isinstance(self.start_time, datetime.datetime):
            raise ValueError("Start time must be a datetime object")
        if not isinstance(self.status, MatchStatus):
            if isinstance(self.status, str):
                try:
                    self.status = MatchStatus(self.status)
                except ValueError:
                    self.status = MatchStatus.UNKNOWN
            else:
                raise ValueError("Status must be a MatchStatus enum")
        if not isinstance(self.score, Score):
            raise ValueError("Score must be a Score object")
        
    def is_live(self) -> bool:
        """Check if match is currently live."""
        return self.status in [MatchStatus.IN_PLAY, MatchStatus.PAUSED]
    
    def is_finished(self) -> bool:
        """Check if match is finished."""
        return self.status == MatchStatus.FINISHED
    
    def is_scheduled(self) -> bool:
        """Check if match is scheduled."""
        return self.status in [MatchStatus.SCHEDULED, MatchStatus.TIMED]
    
    def is_postponed(self) -> bool:
        """Check if match is postponed."""
        return self.status in [MatchStatus.POSTPONED, MatchStatus.CANCELLED, MatchStatus.SUSPENDED]
    
    def __str__(self) -> str:
        """String representation of match."""
        return f"{self.home_team.name} {self.score} {self.away_team.name} ({self.status.value})"


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
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    
    def __post_init__(self):
        """Validate and normalize event data."""
        if not self.id:
            raise ValueError("Event ID is required")
        if not self.match_id:
            raise ValueError("Match ID is required")
        if not isinstance(self.type, EventType):
            if isinstance(self.type, str):
                try:
                    self.type = EventType(self.type)
                except ValueError:
                    self.type = EventType.OTHER
            else:
                raise ValueError("Type must be an EventType enum")
        if not isinstance(self.timestamp, datetime.datetime):
            raise ValueError("Timestamp must be a datetime object")
    
    def __str__(self) -> str:
        """String representation of event."""
        if self.minute is not None:
            return f"{self.minute}' - {self.type.value}: {self.description or ''}"
        return f"{self.type.value}: {self.description or ''}"
