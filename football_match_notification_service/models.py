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
    home: Optional[int] = 0
    away: Optional[int] = 0
    
    def __str__(self) -> str:
        """String representation of score."""
        home_score = self.home if self.home is not None else "-"
        away_score = self.away if self.away is not None else "-"
        return f"{home_score}-{away_score}"


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
        
    def to_dict(self) -> Dict:
        """Convert the Event object to a dictionary."""
        return {
            "id": self.id,
            "match_id": self.match_id,
            "type": self.type.value,
            "minute": self.minute,
            "team_id": self.team_id,
            "player_name": self.player_name,
            "description": self.description,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Event":
        """Create an Event object from a dictionary."""
        timestamp = datetime.datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None
        
        return cls(
            id=data["id"],
            match_id=data["match_id"],
            type=data["type"],
            minute=data.get("minute"),
            team_id=data.get("team_id"),
            player_name=data.get("player_name"),
            description=data.get("description"),
            timestamp=timestamp or datetime.datetime.now(),
        )


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
    events: List[Event] = field(default_factory=list)
    
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
    
    def to_dict(self) -> Dict:
        """Convert the Match object to a dictionary."""
        return {
            "id": self.id,
            "home_team": {
                "id": self.home_team.id,
                "name": self.home_team.name,
                "short_name": self.home_team.short_name,
                "logo_url": self.home_team.logo_url,
                "country": self.home_team.country,
            },
            "away_team": {
                "id": self.away_team.id,
                "name": self.away_team.name,
                "short_name": self.away_team.short_name,
                "logo_url": self.away_team.logo_url,
                "country": self.away_team.country,
            },
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "status": self.status.value,
            "score": {
                "home": self.score.home,
                "away": self.score.away,
            },
            "competition": self.competition,
            "matchday": self.matchday,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "events": [event.to_dict() for event in self.events] if self.events else [],
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Match":
        """Create a Match object from a dictionary."""
        home_team = Team(
            id=data["home_team"]["id"],
            name=data["home_team"]["name"],
            short_name=data["home_team"].get("short_name"),
            logo_url=data["home_team"].get("logo_url"),
            country=data["home_team"].get("country"),
        )
        away_team = Team(
            id=data["away_team"]["id"],
            name=data["away_team"]["name"],
            short_name=data["away_team"].get("short_name"),
            logo_url=data["away_team"].get("logo_url"),
            country=data["away_team"].get("country"),
        )
        
        start_time = datetime.datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None
        last_updated = datetime.datetime.fromisoformat(data["last_updated"]) if data.get("last_updated") else None
        
        score = Score(
            home=data["score"].get("home"),
            away=data["score"].get("away"),
        )
        
        events = []
        if data.get("events"):
            for event_data in data["events"]:
                events.append(Event.from_dict(event_data))
        
        return cls(
            id=data["id"],
            home_team=home_team,
            away_team=away_team,
            start_time=start_time,
            status=data["status"],
            score=score,
            competition=data.get("competition"),
            matchday=data.get("matchday"),
            last_updated=last_updated,
            events=events,
        )
