"""
Tests for data models.
"""

import datetime
import unittest

import pytest

from football_match_notification_service.models import (
    Event,
    EventType,
    Match,
    MatchStatus,
    Score,
    Team,
)


class TestTeam(unittest.TestCase):
    """Test cases for Team model."""

    def test_valid_team(self):
        """Test creating a valid team."""
        team = Team(id="123", name="Test Team")
        assert team.id == "123"
        assert team.name == "Test Team"
        assert team.short_name == "Test Team"  # Default to name
        assert team.logo_url is None
        assert team.country is None

    def test_team_with_all_fields(self):
        """Test creating a team with all fields."""
        team = Team(
            id="123",
            name="Test Team",
            short_name="TT",
            logo_url="https://example.com/logo.png",
            country="Test Country",
        )
        assert team.id == "123"
        assert team.name == "Test Team"
        assert team.short_name == "TT"
        assert team.logo_url == "https://example.com/logo.png"
        assert team.country == "Test Country"

    def test_team_without_id(self):
        """Test creating a team without ID."""
        with pytest.raises(ValueError):
            Team(id="", name="Test Team")

    def test_team_without_name(self):
        """Test creating a team without name."""
        with pytest.raises(ValueError):
            Team(id="123", name="")


class TestScore(unittest.TestCase):
    """Test cases for Score model."""

    def test_default_score(self):
        """Test default score."""
        score = Score()
        assert score.home == 0
        assert score.away == 0
        assert str(score) == "0-0"

    def test_custom_score(self):
        """Test custom score."""
        score = Score(home=2, away=1)
        assert score.home == 2
        assert score.away == 1
        assert str(score) == "2-1"


class TestMatch(unittest.TestCase):
    """Test cases for Match model."""

    def setUp(self):
        """Set up test fixtures."""
        self.home_team = Team(id="1", name="Home Team")
        self.away_team = Team(id="2", name="Away Team")
        self.start_time = datetime.datetime.now()

    def test_valid_match(self):
        """Test creating a valid match."""
        match = Match(
            id="123",
            home_team=self.home_team,
            away_team=self.away_team,
            start_time=self.start_time,
        )
        assert match.id == "123"
        assert match.home_team == self.home_team
        assert match.away_team == self.away_team
        assert match.start_time == self.start_time
        assert match.status == MatchStatus.SCHEDULED
        assert match.score.home == 0
        assert match.score.away == 0
        assert match.competition is None
        assert match.matchday is None
        assert match.last_updated is None
        assert match.events == []

    def test_match_with_all_fields(self):
        """Test creating a match with all fields."""
        score = Score(home=2, away=1)
        events = [
            Event(id="1", match_id="123", type=EventType.GOAL),
            Event(id="2", match_id="123", type=EventType.YELLOW_CARD),
        ]
        match = Match(
            id="123",
            home_team=self.home_team,
            away_team=self.away_team,
            start_time=self.start_time,
            status=MatchStatus.IN_PLAY,
            score=score,
            competition="Test League",
            matchday=5,
            last_updated=self.start_time,
            events=events,
        )
        assert match.id == "123"
        assert match.home_team == self.home_team
        assert match.away_team == self.away_team
        assert match.start_time == self.start_time
        assert match.status == MatchStatus.IN_PLAY
        assert match.score == score
        assert match.competition == "Test League"
        assert match.matchday == 5
        assert match.last_updated == self.start_time
        assert match.events == events

    def test_match_without_id(self):
        """Test creating a match without ID."""
        with pytest.raises(ValueError):
            Match(
                id="",
                home_team=self.home_team,
                away_team=self.away_team,
                start_time=self.start_time,
            )

    def test_match_with_invalid_home_team(self):
        """Test creating a match with invalid home team."""
        with pytest.raises(ValueError):
            Match(
                id="123",
                home_team="Invalid Team",  # Not a Team object
                away_team=self.away_team,
                start_time=self.start_time,
            )

    def test_match_with_invalid_away_team(self):
        """Test creating a match with invalid away team."""
        with pytest.raises(ValueError):
            Match(
                id="123",
                home_team=self.home_team,
                away_team="Invalid Team",  # Not a Team object
                start_time=self.start_time,
            )

    def test_match_with_invalid_start_time(self):
        """Test creating a match with invalid start time."""
        with pytest.raises(ValueError):
            Match(
                id="123",
                home_team=self.home_team,
                away_team=self.away_team,
                start_time="2025-04-11",  # Not a datetime object
            )

    def test_match_with_string_status(self):
        """Test creating a match with string status."""
        match = Match(
            id="123",
            home_team=self.home_team,
            away_team=self.away_team,
            start_time=self.start_time,
            status="IN_PLAY",
        )
        assert match.status == MatchStatus.IN_PLAY

    def test_match_with_invalid_status(self):
        """Test creating a match with invalid status."""
        match = Match(
            id="123",
            home_team=self.home_team,
            away_team=self.away_team,
            start_time=self.start_time,
            status="INVALID_STATUS",
        )
        assert match.status == MatchStatus.UNKNOWN

    def test_match_with_invalid_score(self):
        """Test creating a match with invalid score."""
        with pytest.raises(ValueError):
            Match(
                id="123",
                home_team=self.home_team,
                away_team=self.away_team,
                start_time=self.start_time,
                score="2-1",  # Not a Score object
            )

    def test_is_live(self):
        """Test is_live method."""
        match1 = Match(
            id="123",
            home_team=self.home_team,
            away_team=self.away_team,
            start_time=self.start_time,
            status=MatchStatus.IN_PLAY,
        )
        match2 = Match(
            id="124",
            home_team=self.home_team,
            away_team=self.away_team,
            start_time=self.start_time,
            status=MatchStatus.PAUSED,
        )
        match3 = Match(
            id="125",
            home_team=self.home_team,
            away_team=self.away_team,
            start_time=self.start_time,
            status=MatchStatus.SCHEDULED,
        )
        assert match1.is_live() is True
        assert match2.is_live() is True
        assert match3.is_live() is False

    def test_is_finished(self):
        """Test is_finished method."""
        match1 = Match(
            id="123",
            home_team=self.home_team,
            away_team=self.away_team,
            start_time=self.start_time,
            status=MatchStatus.FINISHED,
        )
        match2 = Match(
            id="124",
            home_team=self.home_team,
            away_team=self.away_team,
            start_time=self.start_time,
            status=MatchStatus.IN_PLAY,
        )
        assert match1.is_finished() is True
        assert match2.is_finished() is False

    def test_is_scheduled(self):
        """Test is_scheduled method."""
        match1 = Match(
            id="123",
            home_team=self.home_team,
            away_team=self.away_team,
            start_time=self.start_time,
            status=MatchStatus.SCHEDULED,
        )
        match2 = Match(
            id="124",
            home_team=self.home_team,
            away_team=self.away_team,
            start_time=self.start_time,
            status=MatchStatus.TIMED,
        )
        match3 = Match(
            id="125",
            home_team=self.home_team,
            away_team=self.away_team,
            start_time=self.start_time,
            status=MatchStatus.IN_PLAY,
        )
        assert match1.is_scheduled() is True
        assert match2.is_scheduled() is True
        assert match3.is_scheduled() is False

    def test_is_postponed(self):
        """Test is_postponed method."""
        match1 = Match(
            id="123",
            home_team=self.home_team,
            away_team=self.away_team,
            start_time=self.start_time,
            status=MatchStatus.POSTPONED,
        )
        match2 = Match(
            id="124",
            home_team=self.home_team,
            away_team=self.away_team,
            start_time=self.start_time,
            status=MatchStatus.CANCELLED,
        )
        match3 = Match(
            id="125",
            home_team=self.home_team,
            away_team=self.away_team,
            start_time=self.start_time,
            status=MatchStatus.SUSPENDED,
        )
        match4 = Match(
            id="126",
            home_team=self.home_team,
            away_team=self.away_team,
            start_time=self.start_time,
            status=MatchStatus.SCHEDULED,
        )
        assert match1.is_postponed() is True
        assert match2.is_postponed() is True
        assert match3.is_postponed() is True
        assert match4.is_postponed() is False

    def test_string_representation(self):
        """Test string representation."""
        match = Match(
            id="123",
            home_team=self.home_team,
            away_team=self.away_team,
            start_time=self.start_time,
            status=MatchStatus.IN_PLAY,
            score=Score(home=2, away=1),
        )
        assert str(match) == "Home Team 2-1 Away Team (IN_PLAY)"


class TestEvent(unittest.TestCase):
    """Test cases for Event model."""

    def test_valid_event(self):
        """Test creating a valid event."""
        event = Event(id="123", match_id="456", type=EventType.GOAL)
        assert event.id == "123"
        assert event.match_id == "456"
        assert event.type == EventType.GOAL
        assert event.minute is None
        assert event.team_id is None
        assert event.player_name is None
        assert event.description is None
        assert isinstance(event.timestamp, datetime.datetime)

    def test_event_with_all_fields(self):
        """Test creating an event with all fields."""
        timestamp = datetime.datetime.now()
        event = Event(
            id="123",
            match_id="456",
            type=EventType.GOAL,
            minute=30,
            team_id="789",
            player_name="Test Player",
            description="Test Description",
            timestamp=timestamp,
        )
        assert event.id == "123"
        assert event.match_id == "456"
        assert event.type == EventType.GOAL
        assert event.minute == 30
        assert event.team_id == "789"
        assert event.player_name == "Test Player"
        assert event.description == "Test Description"
        assert event.timestamp == timestamp

    def test_event_without_id(self):
        """Test creating an event without ID."""
        with pytest.raises(ValueError):
            Event(id="", match_id="456", type=EventType.GOAL)

    def test_event_without_match_id(self):
        """Test creating an event without match ID."""
        with pytest.raises(ValueError):
            Event(id="123", match_id="", type=EventType.GOAL)

    def test_event_with_string_type(self):
        """Test creating an event with string type."""
        event = Event(id="123", match_id="456", type="GOAL")
        assert event.type == EventType.GOAL

    def test_event_with_invalid_type(self):
        """Test creating an event with invalid type."""
        event = Event(id="123", match_id="456", type="INVALID_TYPE")
        assert event.type == EventType.OTHER

    def test_event_with_invalid_timestamp(self):
        """Test creating an event with invalid timestamp."""
        with pytest.raises(ValueError):
            Event(
                id="123",
                match_id="456",
                type=EventType.GOAL,
                timestamp="2025-04-11",  # Not a datetime object
            )

    def test_string_representation_with_minute(self):
        """Test string representation with minute."""
        event = Event(
            id="123",
            match_id="456",
            type=EventType.GOAL,
            minute=30,
            description="Test Description",
        )
        assert str(event) == "30' - GOAL: Test Description"

    def test_string_representation_without_minute(self):
        """Test string representation without minute."""
        event = Event(
            id="123",
            match_id="456",
            type=EventType.MATCH_START,
            description="Test Description",
        )
        assert str(event) == "MATCH_START: Test Description"

    def test_string_representation_without_description(self):
        """Test string representation without description."""
        event = Event(
            id="123",
            match_id="456",
            type=EventType.GOAL,
            minute=30,
        )
        assert str(event) == "30' - GOAL: "
