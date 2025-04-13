"""
Tests for the event detector module.
"""

import pytest
from datetime import datetime, timedelta

from football_match_notification_service.models import (
    Event,
    EventType,
    Match,
    Team,
    Score,
    MatchStatus,
)
from football_match_notification_service.event_detector import EventDetector


@pytest.fixture
def teams():
    """Create test teams."""
    home_team = Team(
        id="1",
        name="Home Team",
        short_name="HOME",
        logo_url="https://example.com/home.png",
        country="Country A",
    )

    away_team = Team(
        id="2",
        name="Away Team",
        short_name="AWAY",
        logo_url="https://example.com/away.png",
        country="Country B",
    )

    return home_team, away_team


@pytest.fixture
def match_factory(teams):
    """Create a factory for match objects with different states."""
    home_team, away_team = teams
    start_time = datetime.now()

    def _create_match(status="SCHEDULED", minute=0, home_score=0, away_score=0):
        # Convert string status to MatchStatus enum
        match_status = status
        if isinstance(status, str):
            try:
                match_status = MatchStatus(status)
            except ValueError:
                match_status = MatchStatus.UNKNOWN

        return Match(
            id="match123",
            home_team=home_team,
            away_team=away_team,
            start_time=start_time,
            status=match_status,
            score=Score(home=home_score, away=away_score),
            competition="Test League",
            minute=minute,
        )

    return _create_match


@pytest.fixture
def event_detector():
    """Create an event detector instance."""
    return EventDetector()


def test_detect_match_start(event_detector, match_factory):
    """Test detection of match start event."""
    # Create a match that has just started
    match = match_factory(status="IN_PLAY", minute=1)

    # Detect events
    events = event_detector.detect_events(match)

    # Verify a match start event was detected
    assert len(events) == 1
    assert events[0].type == EventType.MATCH_START
    assert events[0].match_id == match.id
    assert "Match started" in events[0].description


def test_detect_match_start_only_once(event_detector, match_factory):
    """Test that match start is only detected once."""
    # Create a match that has just started
    match1 = match_factory(status="IN_PLAY", minute=1)

    # Detect events - should find match start
    events1 = event_detector.detect_events(match1)
    assert len(events1) == 1
    assert events1[0].type == EventType.MATCH_START

    # Update the match but keep it in play
    match2 = match_factory(status="IN_PLAY", minute=5)

    # Detect events again - should not find another match start
    events2 = event_detector.detect_events(match2)
    assert len(events2) == 0


def test_detect_half_time(event_detector, match_factory):
    """Test detection of half-time event."""
    # Reset the detector to start fresh
    event_detector.reset()

    # Create a match that is in play
    match1 = match_factory(status="IN_PLAY", minute=44)

    # First detection - no half time yet
    event_detector.detect_events(match1)

    # Update the match to half-time - use the enum directly
    match2 = match_factory(status=MatchStatus.HALF_TIME, minute=45)

    # Debug the match objects
    print(f"Match1 status: {match1.status}, Match2 status: {match2.status}")

    # Detect events again - should find half-time
    events = event_detector.detect_events(match2)

    # Debug output
    print(f"Events detected: {events}")

    assert len(events) == 1
    assert events[0].type == EventType.HALF_TIME
    assert events[0].match_id == match2.id
    assert "Half-time" in events[0].description


def test_detect_match_end(event_detector, match_factory):
    """Test detection of match end event."""
    # Reset the detector to start fresh
    event_detector.reset()

    # Create a match that is in play
    match1 = match_factory(status="IN_PLAY", minute=89)

    # First detection - no match end yet
    event_detector.detect_events(match1)

    # Update the match to finished
    match2 = match_factory(status="FINISHED", minute=90)

    # Detect events again - should find match end
    events = event_detector.detect_events(match2)

    # Debug output
    print(f"Events detected: {events}")

    assert len(events) == 1
    assert events[0].type == EventType.MATCH_END
    assert events[0].match_id == match2.id
    assert "Match ended" in events[0].description


def test_detect_home_goal(event_detector, match_factory):
    """Test detection of a goal by the home team."""
    # Create a match with no goals
    match1 = match_factory(status="IN_PLAY", minute=10, home_score=0, away_score=0)

    # First detection - no goals yet
    event_detector.detect_events(match1)

    # Update the match with a home goal
    match2 = match_factory(status="IN_PLAY", minute=15, home_score=1, away_score=0)

    # Detect events again - should find a goal
    events = event_detector.detect_events(match2)

    assert len(events) == 1
    assert events[0].type == EventType.GOAL
    assert events[0].match_id == match2.id
    assert events[0].team_id == match2.home_team.id
    assert "GOAL" in events[0].description
    assert "1-0" in events[0].description


def test_detect_away_goal(event_detector, match_factory):
    """Test detection of a goal by the away team."""
    # Create a match with no goals
    match1 = match_factory(status="IN_PLAY", minute=20, home_score=0, away_score=0)

    # First detection - no goals yet
    event_detector.detect_events(match1)

    # Update the match with an away goal
    match2 = match_factory(status="IN_PLAY", minute=25, home_score=0, away_score=1)

    # Detect events again - should find a goal
    events = event_detector.detect_events(match2)

    assert len(events) == 1
    assert events[0].type == EventType.GOAL
    assert events[0].match_id == match2.id
    assert events[0].team_id == match2.away_team.id
    assert "GOAL" in events[0].description
    assert "0-1" in events[0].description


def test_detect_multiple_goals(event_detector, match_factory):
    """Test detection of multiple goals in one update."""
    # Create a match with no goals
    match1 = match_factory(status="IN_PLAY", minute=30, home_score=0, away_score=0)

    # First detection - no goals yet
    event_detector.detect_events(match1)

    # Update the match with multiple goals
    match2 = match_factory(status="IN_PLAY", minute=40, home_score=2, away_score=1)

    # Detect events again - should find multiple goals
    events = event_detector.detect_events(match2)

    assert len(events) == 3

    # Check that we have 2 home goals and 1 away goal
    home_goals = [e for e in events if e.team_id == match2.home_team.id]
    away_goals = [e for e in events if e.team_id == match2.away_team.id]

    assert len(home_goals) == 2
    assert len(away_goals) == 1


def test_detect_goals_on_first_update(event_detector, match_factory):
    """Test detection of goals when seeing a match for the first time."""
    # Create a match with existing goals
    match = match_factory(status="IN_PLAY", minute=30, home_score=2, away_score=1)

    # Detect events - should find all existing goals
    events = event_detector.detect_events(match)

    assert len(events) == 4  # 2 home goals + 1 away goal + match start

    # Check event types
    event_types = [e.type for e in events]
    assert EventType.MATCH_START in event_types
    assert event_types.count(EventType.GOAL) == 3


def test_reset_detector(event_detector, match_factory):
    """Test resetting the event detector."""
    # Create a match and detect events
    match1 = match_factory(status="IN_PLAY", minute=10, home_score=1, away_score=0)
    events1 = event_detector.detect_events(match1)
    assert len(events1) > 0

    # Reset the detector
    event_detector.reset()

    # The same match should generate events again after reset
    events2 = event_detector.detect_events(match1)
    assert len(events2) > 0


def test_no_duplicate_events(event_detector, match_factory):
    """Test that the same event is not detected multiple times."""
    # Create a match with a goal
    match = match_factory(status="IN_PLAY", minute=10, home_score=1, away_score=0)

    # Detect events - should find match start and goal
    events1 = event_detector.detect_events(match)
    assert len(events1) > 0

    # Detect events again with the same match state
    events2 = event_detector.detect_events(match)
    assert len(events2) == 0  # No new events should be detected
