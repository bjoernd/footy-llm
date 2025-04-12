"""
Tests for the match tracker module.
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from football_match_notification_service.match_tracker import MatchTracker, get_match_tracker
from football_match_notification_service.models import Match, Team, Score, MatchStatus


class TestMatchTracker:
    """Tests for the MatchTracker class."""

    @pytest.fixture
    def mock_api_client(self):
        """Create a mock API client."""
        mock_client = MagicMock()
        return mock_client

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration manager."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "teams": [
                {"team_id": "1", "name": "Team A", "short_name": "TA", "country": "Country A"},
                {"team_id": "2", "name": "Team B", "short_name": "TB", "country": "Country B"},
            ],
            "polling.discovery_days": 3,
            "polling.match_retention_days": 7,
        }.get(key, default)
        return mock_config

    @pytest.fixture
    def temp_storage_path(self):
        """Create a temporary directory for match storage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def tracker(self, mock_api_client, mock_config, temp_storage_path):
        """Create a match tracker instance."""
        return MatchTracker(
            api_client=mock_api_client,
            config=mock_config,
            storage_path=temp_storage_path,
        )

    def test_init(self, tracker, mock_api_client, mock_config):
        """Test MatchTracker initialization."""
        assert tracker.api_client == mock_api_client
        assert tracker.config == mock_config
        assert len(tracker.teams_to_track) == 2
        assert tracker.team_ids == {"1", "2"}
        assert tracker.discovery_days == 3
        assert tracker.match_retention_days == 7
        assert isinstance(tracker.storage_path, Path)
        assert tracker.storage_path.exists()

    def test_get_teams_to_track(self, tracker):
        """Test _get_teams_to_track method."""
        teams = tracker.teams_to_track
        assert len(teams) == 2
        assert teams[0].id == "1"
        assert teams[0].name == "Team A"
        assert teams[0].short_name == "TA"
        assert teams[0].country == "Country A"
        assert teams[1].id == "2"
        assert teams[1].name == "Team B"
        assert teams[1].short_name == "TB"
        assert teams[1].country == "Country B"

    def test_discover_matches(self, tracker, mock_api_client):
        """Test discover_matches method."""
        # Mock API response
        mock_api_client.get_team_matches.return_value = {
            "matches": [
                {
                    "id": 1,
                    "homeTeam": {"id": 1, "name": "Team A"},
                    "awayTeam": {"id": 3, "name": "Team C"},
                    "utcDate": (datetime.now() + timedelta(days=1)).isoformat(),
                    "status": "SCHEDULED",
                    "score": {"fullTime": {"home": None, "away": None}},
                    "competition": {"id": 1, "name": "Competition A"},
                },
                {
                    "id": 2,
                    "homeTeam": {"id": 3, "name": "Team C"},
                    "awayTeam": {"id": 2, "name": "Team B"},
                    "utcDate": (datetime.now() + timedelta(days=2)).isoformat(),
                    "status": "SCHEDULED",
                    "score": {"fullTime": {"home": None, "away": None}},
                    "competition": {"id": 1, "name": "Competition A"},
                },
            ]
        }

        # Call discover_matches
        new_matches = tracker.discover_matches()

        # Verify API calls
        assert mock_api_client.get_team_matches.call_count == 2
        
        # Verify discovered matches
        assert len(new_matches) == 2
        assert len(tracker.upcoming_matches) == 2
        assert "1" in tracker.upcoming_matches
        assert "2" in tracker.upcoming_matches

    def test_update_match_status_unknown_match(self, tracker):
        """Test update_match_status with unknown match ID."""
        result, changed = tracker.update_match_status("999")
        assert result is None
        assert changed is False

    def test_update_match_status_to_in_play(self, tracker, mock_api_client):
        """Test updating match status from scheduled to in play."""
        # Add a match to upcoming_matches
        home_team = Team(id="1", name="Team A")
        away_team = Team(id="2", name="Team B")
        match = Match(
            id="1",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.now() + timedelta(minutes=30),
            status="SCHEDULED",
            score=Score(home=None, away=None),
            competition="Competition A",
        )
        tracker.upcoming_matches["1"] = match

        # Mock API response for updated match
        mock_api_client.get_match.return_value = {
            "id": 1,
            "homeTeam": {"id": 1, "name": "Team A"},
            "awayTeam": {"id": 2, "name": "Team B"},
            "utcDate": datetime.now().isoformat(),
            "status": "IN_PLAY",
            "score": {"fullTime": {"home": 1, "away": 0}},
            "competition": {"id": 1, "name": "Competition A"},
        }

        # Update match status
        updated_match, status_changed = tracker.update_match_status("1")

        # Verify results
        assert updated_match is not None
        assert status_changed is True
        assert updated_match.status == MatchStatus.IN_PLAY
        assert updated_match.score.home == 1
        assert updated_match.score.away == 0
        assert "1" not in tracker.upcoming_matches
        assert "1" in tracker.active_matches
        assert "1" in tracker.active_matches

    def test_update_match_status_to_finished(self, tracker, mock_api_client):
        """Test updating match status from in play to finished."""
        # Add a match to active_matches
        home_team = Team(id="1", name="Team A")
        away_team = Team(id="2", name="Team B")
        match = Match(
            id="1",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.now() - timedelta(hours=1),
            status="IN_PLAY",
            score=Score(home=1, away=0),
            competition="Competition A",
        )
        tracker.active_matches["1"] = match

        # Mock API response for updated match
        mock_api_client.get_match.return_value = {
            "id": 1,
            "homeTeam": {"id": 1, "name": "Team A"},
            "awayTeam": {"id": 2, "name": "Team B"},
            "utcDate": (datetime.now() - timedelta(hours=1)).isoformat(),
            "status": "FINISHED",
            "score": {"fullTime": {"home": 2, "away": 1}},
            "competition": {"id": 1, "name": "Competition A"},
        }

        # Update match status
        updated_match, status_changed = tracker.update_match_status("1")

        # Verify results
        assert updated_match is not None
        assert status_changed is True
        assert updated_match.status == MatchStatus.FINISHED
        assert updated_match.score.home == 2
        assert updated_match.score.away == 1
        assert "1" not in tracker.active_matches
        assert "1" in tracker.recent_matches
        assert "1" not in tracker.active_matches
        assert "1" in tracker.recent_matches

    def test_get_matches_to_monitor(self, tracker):
        """Test get_matches_to_monitor method."""
        # Add matches to collections
        home_team = Team(id="1", name="Team A")
        away_team = Team(id="2", name="Team B")
        
        # Active match
        active_match = Match(
            id="1",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.now() - timedelta(minutes=30),
            status="IN_PLAY",
            score=Score(home=1, away=0),
            competition="Competition A",
        )
        tracker.active_matches["1"] = active_match
        
        # Upcoming match starting soon
        upcoming_soon = Match(
            id="2",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.now() + timedelta(minutes=15),
            status="SCHEDULED",
            score=Score(home=None, away=None),
            competition="Competition A",
        )
        tracker.upcoming_matches["2"] = upcoming_soon
        
        # Upcoming match not starting soon
        upcoming_later = Match(
            id="3",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.now() + timedelta(hours=2),
            status="SCHEDULED",
            score=Score(home=None, away=None),
            competition="Competition A",
        )
        tracker.upcoming_matches["3"] = upcoming_later
        
        # Recent match
        recent_match = Match(
            id="4",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.now() - timedelta(days=1),
            status="FINISHED",
            score=Score(home=2, away=1),
            competition="Competition A",
        )
        tracker.recent_matches["4"] = recent_match
        
        # Get matches to monitor
        matches_to_monitor = tracker.get_matches_to_monitor()
        
        # Verify results
        assert len(matches_to_monitor) == 2
        match_ids = [m.id for m in matches_to_monitor]
        assert "1" in match_ids  # Active match
        assert "2" in match_ids  # Upcoming soon
        assert "3" not in match_ids  # Not starting soon
        assert "4" not in match_ids  # Recent match

    def test_clean_old_matches(self, tracker):
        """Test clean_old_matches method."""
        # Add old and recent matches
        home_team = Team(id="1", name="Team A")
        away_team = Team(id="2", name="Team B")
        
        # Old match (beyond retention period)
        old_match = Match(
            id="1",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.now() - timedelta(days=10),
            status="FINISHED",
            score=Score(home=2, away=1),
            competition="Competition A",
        )
        tracker.recent_matches["1"] = old_match
        
        # Recent match (within retention period)
        recent_match = Match(
            id="2",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.now() - timedelta(days=3),
            status="FINISHED",
            score=Score(home=1, away=1),
            competition="Competition A",
        )
        tracker.recent_matches["2"] = recent_match
        
        # Clean old matches
        removed_count = tracker.clean_old_matches()
        
        # Verify results
        assert removed_count == 1
        assert "1" not in tracker.recent_matches
        assert "2" in tracker.recent_matches

    def test_save_and_load_matches(self, tracker, temp_storage_path):
        """Test saving and loading matches."""
        # Add matches to collections
        home_team = Team(id="1", name="Team A")
        away_team = Team(id="2", name="Team B")
        
        upcoming_match = Match(
            id="1",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.now() + timedelta(days=1),
            status="SCHEDULED",
            score=Score(home=None, away=None),
            competition="Competition A",
        )
        tracker.upcoming_matches["1"] = upcoming_match
        
        active_match = Match(
            id="2",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.now() - timedelta(minutes=30),
            status="IN_PLAY",
            score=Score(home=1, away=0),
            competition="Competition A",
        )
        tracker.active_matches["2"] = active_match
        
        recent_match = Match(
            id="3",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.now() - timedelta(days=1),
            status="FINISHED",
            score=Score(home=2, away=1),
            competition="Competition A",
        )
        tracker.recent_matches["3"] = recent_match
        
        # Save matches
        tracker._save_matches()
        
        # Verify files were created
        assert os.path.exists(os.path.join(temp_storage_path, "upcoming_matches.json"))
        assert os.path.exists(os.path.join(temp_storage_path, "active_matches.json"))
        assert os.path.exists(os.path.join(temp_storage_path, "recent_matches.json"))
        
        # Clear collections
        tracker.upcoming_matches = {}
        tracker.active_matches = {}
        tracker.recent_matches = {}
        
        # Load matches
        tracker._load_matches()
        
        # Verify matches were loaded
        assert "1" in tracker.upcoming_matches
        assert "2" in tracker.active_matches
        assert "3" in tracker.recent_matches

    def test_get_match(self, tracker):
        """Test get_match method."""
        # Add matches to collections
        home_team = Team(id="1", name="Team A")
        away_team = Team(id="2", name="Team B")
        
        upcoming_match = Match(
            id="1",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.now() + timedelta(days=1),
            status="SCHEDULED",
            score=Score(home=None, away=None),
            competition="Competition A",
        )
        tracker.upcoming_matches["1"] = upcoming_match
        
        active_match = Match(
            id="2",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.now() - timedelta(minutes=30),
            status="IN_PLAY",
            score=Score(home=1, away=0),
            competition="Competition A",
        )
        tracker.active_matches["2"] = active_match
        
        recent_match = Match(
            id="3",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.now() - timedelta(days=1),
            status="FINISHED",
            score=Score(home=2, away=1),
            competition="Competition A",
        )
        tracker.recent_matches["3"] = recent_match
        
        # Get matches
        match1 = tracker.get_match("1")
        match2 = tracker.get_match("2")
        match3 = tracker.get_match("3")
        match4 = tracker.get_match("4")
        
        # Verify results
        assert match1 == upcoming_match
        assert match2 == active_match
        assert match3 == recent_match
        assert match4 is None

    def test_get_all_matches(self, tracker):
        """Test get_all_matches method."""
        # Add matches to collections
        home_team = Team(id="1", name="Team A")
        away_team = Team(id="2", name="Team B")
        
        upcoming_match = Match(
            id="1",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.now() + timedelta(days=1),
            status="SCHEDULED",
            score=Score(home=None, away=None),
            competition="Competition A",
        )
        tracker.upcoming_matches["1"] = upcoming_match
        
        active_match = Match(
            id="2",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.now() - timedelta(minutes=30),
            status="IN_PLAY",
            score=Score(home=1, away=0),
            competition="Competition A",
        )
        tracker.active_matches["2"] = active_match
        
        recent_match = Match(
            id="3",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.now() - timedelta(days=1),
            status="FINISHED",
            score=Score(home=2, away=1),
            competition="Competition A",
        )
        tracker.recent_matches["3"] = recent_match
        
        # Get all matches
        all_matches = tracker.get_all_matches()
        
        # Verify results
        assert len(all_matches["upcoming"]) == 1
        assert len(all_matches["active"]) == 1
        assert len(all_matches["recent"]) == 1
        assert all_matches["upcoming"][0] == upcoming_match
        assert all_matches["active"][0] == active_match
        assert all_matches["recent"][0] == recent_match


@patch("football_match_notification_service.match_tracker.MatchTracker")
def test_get_match_tracker(mock_tracker_class):
    """Test get_match_tracker function."""
    # First call should create a new instance
    mock_api_client = MagicMock()
    mock_config = MagicMock()
    
    tracker = get_match_tracker(
        api_client=mock_api_client,
        config=mock_config,
        storage_path="/tmp/test",
    )
    
    # Verify instance was created with correct parameters
    mock_tracker_class.assert_called_once_with(
        api_client=mock_api_client,
        config=mock_config,
        storage_path="/tmp/test",
    )
    
    # Reset mock
    mock_tracker_class.reset_mock()
    
    # Second call should return the same instance
    tracker2 = get_match_tracker()
    
    # Verify no new instance was created
    mock_tracker_class.assert_not_called()
    assert tracker == tracker2
