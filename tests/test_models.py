"""
Tests for the data models module.
"""

import datetime
from unittest.mock import MagicMock

import pytest

from football_match_notification_service.models import (
    Event,
    EventType,
    Match,
    MatchStatus,
    Score,
    Team,
)


class TestTeam:
    """Tests for the Team model."""

    def test_team_creation(self):
        """Test creating a team."""
        team = Team(id="123", name="Test Team", short_name="TEST", logo_url="http://example.com/logo.png", country="Test Country")
        assert team.id == "123"
        assert team.name == "Test Team"
        assert team.short_name == "TEST"
        assert team.logo_url == "http://example.com/logo.png"
        assert team.country == "Test Country"

    def test_team_from_api_football(self):
        """Test creating a team from API-Football data."""
        team_data = {
            "id": 123,
            "name": "Test Team",
            "code": "TEST",
            "logo": "http://example.com/logo.png",
            "country": "Test Country"
        }
        team = Team.from_api_football(team_data)
        assert team.id == "123"
        assert team.name == "Test Team"
        assert team.short_name == "TEST"
        assert team.logo_url == "http://example.com/logo.png"
        assert team.country == "Test Country"

    def test_team_from_api_football_minimal(self):
        """Test creating a team from minimal API-Football data."""
        team_data = {
            "id": 123,
            "name": "Test Team"
        }
        team = Team.from_api_football(team_data)
        assert team.id == "123"
        assert team.name == "Test Team"
        assert team.short_name is None
        assert team.logo_url is None
        assert team.country is None

    def test_team_from_api_football_empty(self):
        """Test creating a team from empty API-Football data."""
        team_data = {}
        team = Team.from_api_football(team_data)
        assert team.id == ""
        assert team.name == ""
        assert team.short_name is None
        assert team.logo_url is None
        assert team.country is None


class TestScore:
    """Tests for the Score model."""

    def test_score_creation(self):
        """Test creating a score."""
        score = Score(home=2, away=1)
        assert score.home == 2
        assert score.away == 1

    def test_score_from_api_football(self):
        """Test creating a score from API-Football data."""
        score_data = {
            "home": 2,
            "away": 1
        }
        score = Score.from_api_football(score_data)
        assert score.home == 2
        assert score.away == 1

    def test_score_from_api_football_empty(self):
        """Test creating a score from empty API-Football data."""
        score_data = {}
        score = Score.from_api_football(score_data)
        assert score.home == 0
        assert score.away == 0

    def test_score_from_api_football_none_values(self):
        """Test creating a score from API-Football data with None values."""
        score_data = {
            "home": None,
            "away": None
        }
        score = Score.from_api_football(score_data)
        assert score.home == 0
        assert score.away == 0


class TestMatchStatus:
    """Tests for the MatchStatus enum."""

    def test_match_status_from_api_football(self):
        """Test converting API-Football status to MatchStatus."""
        assert MatchStatus.from_api_football("NS") == MatchStatus.SCHEDULED
        assert MatchStatus.from_api_football("1H") == MatchStatus.IN_PLAY
        assert MatchStatus.from_api_football("HT") == MatchStatus.HALF_TIME
        assert MatchStatus.from_api_football("2H") == MatchStatus.IN_PLAY
        assert MatchStatus.from_api_football("FT") == MatchStatus.FINISHED
        assert MatchStatus.from_api_football("AET") == MatchStatus.FINISHED
        assert MatchStatus.from_api_football("PEN") == MatchStatus.FINISHED
        assert MatchStatus.from_api_football("PST") == MatchStatus.POSTPONED
        assert MatchStatus.from_api_football("CANC") == MatchStatus.CANCELLED
        assert MatchStatus.from_api_football("UNKNOWN_STATUS") == MatchStatus.UNKNOWN


class TestEventType:
    """Tests for the EventType enum."""

    def test_event_type_from_api_football(self):
        """Test converting API-Football event type to EventType."""
        assert EventType.from_api_football("Goal") == EventType.GOAL
        assert EventType.from_api_football("Card") == EventType.YELLOW_CARD
        assert EventType.from_api_football("Subst") == EventType.SUBSTITUTION
        assert EventType.from_api_football("Penalty missed") == EventType.PENALTY_MISSED
        assert EventType.from_api_football("UNKNOWN_TYPE") == EventType.OTHER


class TestMatch:
    """Tests for the Match model."""

    def test_match_creation(self):
        """Test creating a match."""
        home_team = Team(id="123", name="Home Team")
        away_team = Team(id="456", name="Away Team")
        score = Score(home=2, away=1)
        start_time = datetime.datetime(2023, 1, 1, 15, 0)
        
        match = Match(
            id="789",
            home_team=home_team,
            away_team=away_team,
            start_time=start_time,
            status=MatchStatus.FINISHED,
            score=score,
            competition="Test League",
            venue="Test Stadium",
            referee="Test Referee",
            round="Round 1",
            season="2023"
        )
        
        assert match.id == "789"
        assert match.home_team == home_team
        assert match.away_team == away_team
        assert match.start_time == start_time
        assert match.status == MatchStatus.FINISHED
        assert match.score == score
        assert match.competition == "Test League"
        assert match.venue == "Test Stadium"
        assert match.referee == "Test Referee"
        assert match.round == "Round 1"
        assert match.season == "2023"

    def test_match_from_api_football(self):
        """Test creating a match from API-Football data."""
        match_data = {
            "fixture": {
                "id": 789,
                "date": "2023-01-01T15:00:00Z",
                "status": {
                    "short": "FT"
                },
                "venue": {
                    "name": "Test Stadium"
                },
                "referee": "Test Referee"
            },
            "teams": {
                "home": {
                    "id": 123,
                    "name": "Home Team"
                },
                "away": {
                    "id": 456,
                    "name": "Away Team"
                }
            },
            "goals": {
                "home": 2,
                "away": 1
            },
            "league": {
                "name": "Test League",
                "round": "Round 1",
                "season": 2023
            }
        }
        
        match = Match.from_api_football(match_data)
        
        assert match.id == "789"
        assert match.home_team.id == "123"
        assert match.home_team.name == "Home Team"
        assert match.away_team.id == "456"
        assert match.away_team.name == "Away Team"
        assert match.start_time.isoformat() == "2023-01-01T15:00:00+00:00"
        assert match.status == MatchStatus.FINISHED
        assert match.score.home == 2
        assert match.score.away == 1
        assert match.competition == "Test League"
        assert match.venue == "Test Stadium"
        assert match.referee == "Test Referee"
        assert match.round == "Round 1"
        assert match.season == "2023"

    def test_match_from_api_football_minimal(self):
        """Test creating a match from minimal API-Football data."""
        match_data = {
            "fixture": {
                "id": 789,
                "status": {}
            },
            "teams": {
                "home": {
                    "id": 123,
                    "name": "Home Team"
                },
                "away": {
                    "id": 456,
                    "name": "Away Team"
                }
            },
            "goals": {},
            "league": {}
        }
        
        match = Match.from_api_football(match_data)
        
        assert match.id == "789"
        assert match.home_team.id == "123"
        assert match.home_team.name == "Home Team"
        assert match.away_team.id == "456"
        assert match.away_team.name == "Away Team"
        assert match.status == MatchStatus.UNKNOWN
        assert match.score.home == 0
        assert match.score.away == 0
        assert match.competition is None
        assert match.venue is None
        assert match.referee is None
        assert match.round is None
        assert match.season is None


class TestEvent:
    """Tests for the Event model."""

    def test_event_creation(self):
        """Test creating an event."""
        event = Event(
            id="123_45_GOAL",
            match_id="123",
            type=EventType.GOAL,
            minute=45,
            team_id="456",
            player_name="Test Player",
            description="Goal scored by Test Player",
            score_home=1,
            score_away=0
        )
        
        assert event.id == "123_45_GOAL"
        assert event.match_id == "123"
        assert event.type == EventType.GOAL
        assert event.minute == 45
        assert event.team_id == "456"
        assert event.player_name == "Test Player"
        assert event.description == "Goal scored by Test Player"
        assert event.score_home == 1
        assert event.score_away == 0

    def test_event_from_api_football(self):
        """Test creating an event from API-Football data."""
        event_data = {
            "time": {
                "elapsed": 45
            },
            "type": "Goal",
            "detail": "Normal Goal",
            "comments": "Great shot",
            "team": {
                "id": 456,
                "name": "Test Team"
            },
            "player": {
                "id": 789,
                "name": "Test Player"
            }
        }
        
        event = Event.from_api_football(event_data, "123")
        
        assert event.id == "123_45_GOAL_456"
        assert event.match_id == "123"
        assert event.type == EventType.GOAL
        assert event.minute == 45
        assert event.team_id == "456"
        assert event.player_name == "Test Player"
        assert event.description == "Test Player - Normal Goal - Great shot"

    def test_event_from_api_football_card(self):
        """Test creating a card event from API-Football data."""
        # Yellow card
        yellow_card_data = {
            "time": {
                "elapsed": 30
            },
            "type": "Card",
            "detail": "Yellow Card",
            "team": {
                "id": 456
            },
            "player": {
                "name": "Test Player"
            }
        }
        
        yellow_event = Event.from_api_football(yellow_card_data, "123")
        assert yellow_event.type == EventType.YELLOW_CARD
        
        # Red card
        red_card_data = {
            "time": {
                "elapsed": 60
            },
            "type": "Card",
            "detail": "Red Card",
            "team": {
                "id": 456
            },
            "player": {
                "name": "Test Player"
            }
        }
        
        red_event = Event.from_api_football(red_card_data, "123")
        assert red_event.type == EventType.RED_CARD

    def test_create_match_start_event(self):
        """Test creating a match start event."""
        home_team = Team(id="123", name="Home Team")
        away_team = Team(id="456", name="Away Team")
        score = Score(home=0, away=0)
        match = Match(
            id="789",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.datetime.now(),
            status=MatchStatus.IN_PLAY,
            score=score
        )
        
        event = Event.create_match_start_event(match)
        
        assert event.id == "789_START"
        assert event.match_id == "789"
        assert event.type == EventType.MATCH_START
        assert event.minute == 0
        assert "Match started" in event.description
        assert "Home Team" in event.description
        assert "Away Team" in event.description
        assert event.score_home == 0
        assert event.score_away == 0

    def test_create_match_end_event(self):
        """Test creating a match end event."""
        home_team = Team(id="123", name="Home Team")
        away_team = Team(id="456", name="Away Team")
        score = Score(home=2, away=1)
        match = Match(
            id="789",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.datetime.now(),
            status=MatchStatus.FINISHED,
            score=score
        )
        
        event = Event.create_match_end_event(match)
        
        assert event.id == "789_END"
        assert event.match_id == "789"
        assert event.type == EventType.MATCH_END
        assert event.minute == 90
        assert "Match ended" in event.description
        assert "Home Team" in event.description
        assert "Away Team" in event.description
        assert "2-1" in event.description
        assert event.score_home == 2
        assert event.score_away == 1

    def test_create_half_time_event(self):
        """Test creating a half-time event."""
        home_team = Team(id="123", name="Home Team")
        away_team = Team(id="456", name="Away Team")
        score = Score(home=1, away=0)
        match = Match(
            id="789",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.datetime.now(),
            status=MatchStatus.HALF_TIME,
            score=score
        )
        
        event = Event.create_half_time_event(match)
        
        assert event.id == "789_HALF_TIME"
        assert event.match_id == "789"
        assert event.type == EventType.HALF_TIME
        assert event.minute == 45
        assert "Half-time" in event.description
        assert "Home Team" in event.description
        assert "Away Team" in event.description
        assert "1-0" in event.description
        assert event.score_home == 1
        assert event.score_away == 0
