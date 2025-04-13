"""
Tests for the event detector module.
"""

import datetime
from unittest.mock import MagicMock, patch

import pytest

from football_match_notification_service.api_client import APIFootballClient
from football_match_notification_service.event_detector import EventDetector
from football_match_notification_service.models import (
    Event,
    EventType,
    Match,
    MatchStatus,
    Score,
    Team,
)


class TestEventDetector:
    """Tests for the event detector."""

    @pytest.fixture
    def mock_api_client(self):
        """Create a mock API client."""
        return MagicMock(spec=APIFootballClient)

    @pytest.fixture
    def event_detector(self, mock_api_client):
        """Create an event detector with mock dependencies."""
        detector = EventDetector(api_client=mock_api_client)
        detector.parser.parse_events = MagicMock(return_value=[])
        return detector

    @pytest.fixture
    def home_team(self):
        """Create a home team fixture."""
        return Team(id="123", name="Home Team")

    @pytest.fixture
    def away_team(self):
        """Create an away team fixture."""
        return Team(id="456", name="Away Team")

    def test_detect_match_start(self, event_detector, home_team, away_team):
        """Test detecting match start."""
        # Create a match that has just started
        match = Match(
            id="789",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.datetime.now(),
            status=MatchStatus.IN_PLAY,
            score=Score(home=0, away=0),
        )

        # Detect events
        events = event_detector.detect_events(match)

        # Verify events
        assert len(events) == 1
        assert events[0].type == EventType.MATCH_START
        assert events[0].match_id == "789"

        # Detect events again (should not detect start again)
        events = event_detector.detect_events(match)
        assert len(events) == 0

    def test_detect_half_time(self, event_detector, home_team, away_team):
        """Test detecting half-time."""
        # Create a match that is in play
        in_play_match = Match(
            id="789",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.datetime.now(),
            status=MatchStatus.IN_PLAY,
            score=Score(home=1, away=0),
        )

        # First detect the in-play match
        event_detector.detect_events(in_play_match)

        # Now create a match at half-time
        half_time_match = Match(
            id="789",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.datetime.now(),
            status=MatchStatus.HALF_TIME,
            score=Score(home=1, away=0),
        )

        # Detect events
        events = event_detector.detect_events(half_time_match)

        # Verify events
        assert len(events) == 1
        assert events[0].type == EventType.HALF_TIME
        assert events[0].match_id == "789"

    def test_detect_match_end(self, event_detector, home_team, away_team):
        """Test detecting match end."""
        # Create a match that is in play
        in_play_match = Match(
            id="789",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.datetime.now(),
            status=MatchStatus.IN_PLAY,
            score=Score(home=2, away=1),
        )

        # First detect the in-play match
        event_detector.detect_events(in_play_match)

        # Now create a match that has finished
        finished_match = Match(
            id="789",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.datetime.now(),
            status=MatchStatus.FINISHED,
            score=Score(home=2, away=1),
        )

        # Detect events
        events = event_detector.detect_events(finished_match)

        # Verify events
        assert len(events) == 1
        assert events[0].type == EventType.MATCH_END
        assert events[0].match_id == "789"

    def test_detect_score_change(self, event_detector, home_team, away_team, mock_api_client):
        """Test detecting score changes."""
        # Create a match with initial score
        initial_match = Match(
            id="789",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.datetime.now(),
            status=MatchStatus.IN_PLAY,
            score=Score(home=0, away=0),
        )

        # First detect the initial match
        event_detector.detect_events(initial_match)

        # Now create a match with updated score
        updated_match = Match(
            id="789",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.datetime.now(),
            status=MatchStatus.IN_PLAY,
            score=Score(home=1, away=0),
        )

        # Mock API response for events
        goal_event = Event(
            id="789_45_GOAL_123",
            match_id="789",
            type=EventType.GOAL,
            minute=45,
            team_id="123",
            player_name="Goal Scorer",
            description="Goal by Goal Scorer",
        )
        event_detector.parser.parse_events.return_value = [goal_event]

        # Detect events
        events = event_detector.detect_events(updated_match)

        # Verify API call
        mock_api_client.get_fixtures_events.assert_called_once_with("789")

        # Verify events
        assert len(events) == 1
        assert events[0].type == EventType.GOAL
        assert events[0].match_id == "789"
        assert events[0].team_id == "123"
        assert events[0].player_name == "Goal Scorer"

    def test_detect_multiple_events(self, event_detector, home_team, away_team):
        """Test detecting multiple events in sequence."""
        # Create a scheduled match
        scheduled_match = Match(
            id="789",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.datetime.now(),
            status=MatchStatus.SCHEDULED,
            score=Score(home=0, away=0),
        )

        # First detect the scheduled match (no events)
        events = event_detector.detect_events(scheduled_match)
        assert len(events) == 0

        # Match starts
        in_play_match = Match(
            id="789",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.datetime.now(),
            status=MatchStatus.IN_PLAY,
            score=Score(home=0, away=0),
        )
        events = event_detector.detect_events(in_play_match)
        assert len(events) == 1
        assert events[0].type == EventType.MATCH_START

        # Half-time
        half_time_match = Match(
            id="789",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.datetime.now(),
            status=MatchStatus.HALF_TIME,
            score=Score(home=0, away=0),
        )
        events = event_detector.detect_events(half_time_match)
        assert len(events) == 1
        assert events[0].type == EventType.HALF_TIME

        # Second half
        second_half_match = Match(
            id="789",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.datetime.now(),
            status=MatchStatus.IN_PLAY,
            score=Score(home=0, away=0),
        )
        events = event_detector.detect_events(second_half_match)
        assert len(events) == 0  # No new events

        # Match ends
        finished_match = Match(
            id="789",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.datetime.now(),
            status=MatchStatus.FINISHED,
            score=Score(home=0, away=0),
        )
        events = event_detector.detect_events(finished_match)
        assert len(events) == 1
        assert events[0].type == EventType.MATCH_END

    def test_clear_match_state(self, event_detector, home_team, away_team):
        """Test clearing match state."""
        # Create a match
        match = Match(
            id="789",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.datetime.now(),
            status=MatchStatus.IN_PLAY,
            score=Score(home=0, away=0),
        )

        # Detect events to populate state
        event_detector.detect_events(match)
        assert "789" in event_detector._previous_states

        # Clear state
        event_detector.clear_match_state("789")
        assert "789" not in event_detector._previous_states

    def test_clear_old_matches(self, event_detector, home_team, away_team):
        """Test clearing old matches."""
        # Create matches with different statuses
        in_play_match = Match(
            id="1",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.datetime.now(),
            status=MatchStatus.IN_PLAY,
            score=Score(home=0, away=0),
        )

        finished_match = Match(
            id="2",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.datetime.now(),
            status=MatchStatus.FINISHED,
            score=Score(home=1, away=0),
        )

        cancelled_match = Match(
            id="3",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.datetime.now(),
            status=MatchStatus.CANCELLED,
            score=Score(home=0, away=0),
        )

        # Populate state
        event_detector.detect_events(in_play_match)
        event_detector.detect_events(finished_match)
        event_detector.detect_events(cancelled_match)

        assert "1" in event_detector._previous_states
        assert "2" in event_detector._previous_states
        assert "3" in event_detector._previous_states

        # Clear old matches
        event_detector.clear_old_matches()

        # Verify only active matches remain
        assert "1" in event_detector._previous_states
        assert "2" not in event_detector._previous_states
        assert "3" not in event_detector._previous_states
