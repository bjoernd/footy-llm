"""
Tests for the match tracker module.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from football_match_notification_service.api_client import APIFootballClient
from football_match_notification_service.config_manager import ConfigManager
from football_match_notification_service.match_tracker import MatchTracker
from football_match_notification_service.models import Match, MatchStatus, Score, Team


class TestMatchTracker:
    """Tests for the match tracker."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration manager."""
        config = MagicMock(spec=ConfigManager)
        config.get.side_effect = lambda key, default=None: {
            "teams": [
                {"name": "Test Team 1", "team_id": "123"},
                {"name": "Test Team 2", "team_id": "456"},
            ],
            "polling_settings.match_discovery_days": 3,
            "polling_settings.match_history_days": 7,
        }.get(key, default)
        config.get_with_default.side_effect = lambda key: {
            "polling_settings.match_discovery_days": 3,
            "polling_settings.match_history_days": 7,
        }.get(key)
        return config

    @pytest.fixture
    def mock_api_client(self):
        """Create a mock API client."""
        return MagicMock(spec=APIFootballClient)

    @pytest.fixture
    def temp_storage_path(self, tmp_path):
        """Create a temporary storage path."""
        return tmp_path / "football_matches"

    @pytest.fixture
    def match_tracker(self, mock_api_client, mock_config, temp_storage_path):
        """Create a match tracker with mock dependencies."""
        with patch("football_match_notification_service.match_tracker.APIFootballParser"):
            tracker = MatchTracker(
                api_client=mock_api_client,
                config=mock_config,
                storage_path=temp_storage_path,
            )
            return tracker

    def test_init(self, match_tracker, temp_storage_path):
        """Test initialization."""
        assert match_tracker.storage_path == temp_storage_path
        assert temp_storage_path.exists()
        assert isinstance(match_tracker.matches, dict)

    def test_discover_matches(self, match_tracker, mock_api_client):
        """Test discovering matches."""
        # Mock API response
        mock_response = {
            "response": [
                {
                    "fixture": {
                        "id": 789,
                        "date": "2023-01-01T15:00:00Z",
                        "status": {"short": "NS"},
                    },
                    "teams": {
                        "home": {"id": 123, "name": "Test Team 1"},
                        "away": {"id": 456, "name": "Test Team 2"},
                    },
                    "goals": {"home": 0, "away": 0},
                    "league": {"name": "Test League"},
                },
            ]
        }
        mock_api_client.get_matches_by_team.return_value = mock_response

        # Create a proper mock match with all required attributes
        home_team = Team(id="123", name="Test Team 1")
        away_team = Team(id="456", name="Test Team 2")
        score = Score(home=0, away=0)
        mock_match = Match(
            id="789",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.now() + timedelta(days=1),
            status=MatchStatus.SCHEDULED,
            score=score
        )

        # Mock parser to return our properly constructed match
        match_tracker.parser.parse_matches.return_value = [mock_match]

        # Call method
        discovered = match_tracker.discover_matches()

        # Verify API calls
        assert mock_api_client.get_matches_by_team.call_count == 2
        mock_api_client.get_matches_by_team.assert_any_call(
            team_id="123",
            from_date=datetime.now().date().strftime("%Y-%m-%d"),
            to_date=(datetime.now().date() + timedelta(days=3)).strftime("%Y-%m-%d"),
        )

        # Verify parser calls
        assert match_tracker.parser.parse_matches.call_count == 2

        # Verify result - we only get one match because the same match is returned for both teams
        assert len(discovered) == 1
        assert "789" in match_tracker.matches

    def test_get_match(self, match_tracker):
        """Test getting a match by ID."""
        # Add a test match
        mock_match = MagicMock(spec=Match)
        mock_match.id = "123"
        match_tracker.matches["123"] = mock_match

        # Get the match
        result = match_tracker.get_match("123")
        assert result == mock_match

        # Try to get a non-existent match
        result = match_tracker.get_match("456")
        assert result is None

    def test_get_matches_by_status(self, match_tracker):
        """Test getting matches by status."""
        # Add test matches
        match1 = MagicMock(spec=Match)
        match1.id = "1"
        match1.status = MatchStatus.IN_PLAY

        match2 = MagicMock(spec=Match)
        match2.id = "2"
        match2.status = MatchStatus.FINISHED

        match3 = MagicMock(spec=Match)
        match3.id = "3"
        match3.status = MatchStatus.IN_PLAY

        match_tracker.matches = {
            "1": match1,
            "2": match2,
            "3": match3,
        }

        # Get matches by status
        in_play = match_tracker.get_matches_by_status(MatchStatus.IN_PLAY)
        finished = match_tracker.get_matches_by_status(MatchStatus.FINISHED)
        scheduled = match_tracker.get_matches_by_status(MatchStatus.SCHEDULED)

        assert len(in_play) == 2
        assert match1 in in_play
        assert match3 in in_play

        assert len(finished) == 1
        assert match2 in finished

        assert len(scheduled) == 0

    def test_get_active_matches(self, match_tracker):
        """Test getting active matches."""
        # Add test matches
        match1 = MagicMock(spec=Match)
        match1.id = "1"
        match1.status = MatchStatus.IN_PLAY

        match2 = MagicMock(spec=Match)
        match2.id = "2"
        match2.status = MatchStatus.FINISHED

        match3 = MagicMock(spec=Match)
        match3.id = "3"
        match3.status = MatchStatus.HALF_TIME

        match4 = MagicMock(spec=Match)
        match4.id = "4"
        match4.status = MatchStatus.SCHEDULED

        match_tracker.matches = {
            "1": match1,
            "2": match2,
            "3": match3,
            "4": match4,
        }

        # Get active matches
        active = match_tracker.get_active_matches()

        assert len(active) == 2
        assert match1 in active
        assert match3 in active

    def test_get_upcoming_matches(self, match_tracker):
        """Test getting upcoming matches."""
        now = datetime.now()

        # Add test matches
        match1 = MagicMock(spec=Match)
        match1.id = "1"
        match1.status = MatchStatus.SCHEDULED
        match1.start_time = now + timedelta(hours=2)

        match2 = MagicMock(spec=Match)
        match2.id = "2"
        match2.status = MatchStatus.SCHEDULED
        match2.start_time = now + timedelta(hours=25)  # Outside 24h window

        match3 = MagicMock(spec=Match)
        match3.id = "3"
        match3.status = MatchStatus.TIMED
        match3.start_time = now + timedelta(hours=12)

        match4 = MagicMock(spec=Match)
        match4.id = "4"
        match4.status = MatchStatus.IN_PLAY  # Not upcoming
        match4.start_time = now - timedelta(hours=1)

        match_tracker.matches = {
            "1": match1,
            "2": match2,
            "3": match3,
            "4": match4,
        }

        # Get upcoming matches (24h window)
        upcoming = match_tracker.get_upcoming_matches(hours=24)

        assert len(upcoming) == 2
        assert match1 in upcoming
        assert match3 in upcoming

    def test_update_match_status(self, match_tracker, mock_api_client):
        """Test updating match status."""
        # Add a test match
        home_team = Team(id="123", name="Home Team")
        away_team = Team(id="456", name="Away Team")
        old_score = Score(home=1, away=0)
        old_match = Match(
            id="123",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.now(),
            status=MatchStatus.IN_PLAY,
            score=old_score
        )

        match_tracker.matches["123"] = old_match

        # Mock API response
        mock_response = {"response": [{"fixture": {"id": 123}}]}
        mock_api_client.get_match_details.return_value = mock_response

        # Create updated match
        new_score = Score(home=2, away=0)
        updated_match = Match(
            id="123",
            home_team=home_team,
            away_team=away_team,
            start_time=datetime.now(),
            status=MatchStatus.FINISHED,  # Status changed
            score=new_score  # Score changed
        )

        match_tracker.parser.parse_matches.return_value = [updated_match]

        # Call method
        with patch.object(match_tracker, 'save_matches') as mock_save:
            result = match_tracker.update_match_status("123")

        # Verify API call
        mock_api_client.get_match_details.assert_called_once_with("123")

        # Verify parser call
        match_tracker.parser.parse_matches.assert_called_once_with(mock_response)

        # Verify result
        assert result == updated_match
        assert match_tracker.matches["123"] == updated_match

    def test_update_match_status_unknown_match(self, match_tracker, mock_api_client):
        """Test updating status of unknown match."""
        result = match_tracker.update_match_status("unknown")
        assert result is None
        mock_api_client.get_match_details.assert_not_called()

    def test_update_active_matches(self, match_tracker):
        """Test updating all active matches."""
        # Mock get_active_matches
        match1 = MagicMock(spec=Match)
        match1.id = "1"
        match2 = MagicMock(spec=Match)
        match2.id = "2"

        with patch.object(match_tracker, "get_active_matches", return_value=[match1, match2]):
            with patch.object(match_tracker, "update_match_status") as mock_update:
                mock_update.side_effect = [match1, match2]

                # Call method
                result = match_tracker.update_active_matches()

                # Verify update calls
                assert mock_update.call_count == 2
                mock_update.assert_any_call("1")
                mock_update.assert_any_call("2")

                # Verify result
                assert len(result) == 2
                assert match1 in result
                assert match2 in result

    def test_clean_old_matches(self, match_tracker):
        """Test cleaning old matches."""
        now = datetime.now()

        # Add test matches
        match1 = MagicMock(spec=Match)
        match1.id = "1"
        match1.status = MatchStatus.FINISHED
        match1.start_time = now - timedelta(days=10)  # Old match

        match2 = MagicMock(spec=Match)
        match2.id = "2"
        match2.status = MatchStatus.FINISHED
        match2.start_time = now - timedelta(days=3)  # Recent match

        match3 = MagicMock(spec=Match)
        match3.id = "3"
        match3.status = MatchStatus.SCHEDULED
        match3.start_time = now - timedelta(days=10)  # Old but not finished

        match_tracker.matches = {
            "1": match1,
            "2": match2,
            "3": match3,
        }

        # Clean old matches (7 days)
        with patch.object(match_tracker, "save_matches") as mock_save:
            removed = match_tracker.clean_old_matches(days=7)

            # Verify result
            assert removed == 1
            assert "1" not in match_tracker.matches
            assert "2" in match_tracker.matches
            assert "3" in match_tracker.matches
            mock_save.assert_called_once()

    def test_save_and_load_matches(self, match_tracker, temp_storage_path):
        """Test saving and loading matches."""
        # Create test matches
        from football_match_notification_service.models import Team, Score, Match, MatchStatus
        
        home_team = Team(id="123", name="Home Team")
        away_team = Team(id="456", name="Away Team")
        score = Score(home=2, away=1)
        start_time = datetime.now()

        match = Match(
            id="789",
            home_team=home_team,
            away_team=away_team,
            start_time=start_time,
            status=MatchStatus.FINISHED,
            score=score,
            competition="Test League",
        )

        # Save match
        match_tracker.matches = {"789": match}
        match_tracker.save_matches()

        # Verify file was created
        matches_file = temp_storage_path / "matches.json"
        assert matches_file.exists()

        # Create a new tracker to load matches
        new_tracker = MatchTracker(
            api_client=match_tracker.api_client,
            config=match_tracker.config,
            storage_path=temp_storage_path,
        )

        # Verify matches were loaded
        assert "789" in new_tracker.matches
        loaded_match = new_tracker.matches["789"]
        assert loaded_match.id == "789"
        assert loaded_match.home_team.id == "123"
        assert loaded_match.home_team.name == "Home Team"
        assert loaded_match.away_team.id == "456"
        assert loaded_match.away_team.name == "Away Team"
        assert loaded_match.status == MatchStatus.FINISHED
        assert loaded_match.score.home == 2
        assert loaded_match.score.away == 1
        assert loaded_match.competition == "Test League"
