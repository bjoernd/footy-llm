"""
Tests for data parsers.
"""

import datetime
import json
import unittest
from unittest.mock import patch

import pytest

from football_match_notification_service.models import (
    Event,
    EventType,
    Match,
    MatchStatus,
    Score,
    Team,
)
from football_match_notification_service.parsers import FootballDataParser, ParserError


class TestFootballDataParser(unittest.TestCase):
    """Test cases for FootballDataParser."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample team data
        self.team_data = {
            "id": 123,
            "name": "Test Team",
            "shortName": "TT",
            "tla": "TTT",
            "crest": "https://example.com/logo.png",
            "area": {"name": "Test Country"},
        }

        # Sample score data
        self.score_data = {
            "fullTime": {"home": 2, "away": 1},
            "halfTime": {"home": 1, "away": 0},
        }

        # Sample match data
        self.match_data = {
            "id": 123,
            "homeTeam": self.team_data,
            "awayTeam": {
                "id": 456,
                "name": "Away Team",
                "shortName": "AT",
                "crest": "https://example.com/away_logo.png",
                "area": {"name": "Away Country"},
            },
            "utcDate": "2025-04-11T15:00:00Z",
            "status": "IN_PLAY",
            "score": self.score_data,
            "competition": {"name": "Test League"},
            "matchday": 5,
        }

        # Sample matches data
        self.matches_data = {
            "matches": [
                self.match_data,
                {
                    "id": 456,
                    "homeTeam": {
                        "id": 789,
                        "name": "Home Team 2",
                    },
                    "awayTeam": {
                        "id": 101,
                        "name": "Away Team 2",
                    },
                    "utcDate": "2025-04-12T15:00:00Z",
                    "status": "SCHEDULED",
                    "score": {"fullTime": {"home": 0, "away": 0}},
                },
            ]
        }

    def test_parse_team(self):
        """Test parsing team data."""
        team = FootballDataParser.parse_team(self.team_data)
        assert isinstance(team, Team)
        assert team.id == "123"
        assert team.name == "Test Team"
        assert team.short_name == "TT"
        assert team.logo_url == "https://example.com/logo.png"
        assert team.country == "Test Country"

    def test_parse_team_minimal(self):
        """Test parsing minimal team data."""
        team_data = {"id": 123, "name": "Test Team"}
        team = FootballDataParser.parse_team(team_data)
        assert isinstance(team, Team)
        assert team.id == "123"
        assert team.name == "Test Team"
        assert team.short_name == "Test Team"  # Default to name
        assert team.logo_url is None
        assert team.country is None

    def test_parse_team_missing_id(self):
        """Test parsing team data with missing ID."""
        team_data = {"name": "Test Team"}
        with pytest.raises(ParserError):
            FootballDataParser.parse_team(team_data)

    def test_parse_team_missing_name(self):
        """Test parsing team data with missing name."""
        team_data = {"id": 123}
        with pytest.raises(ParserError):
            FootballDataParser.parse_team(team_data)

    def test_parse_score(self):
        """Test parsing score data."""
        score = FootballDataParser.parse_score(self.score_data)
        assert isinstance(score, Score)
        assert score.home == 2
        assert score.away == 1

    def test_parse_score_minimal(self):
        """Test parsing minimal score data."""
        score_data = {"home": 2, "away": 1}
        score = FootballDataParser.parse_score(score_data)
        assert isinstance(score, Score)
        assert score.home == 2
        assert score.away == 1

    def test_parse_score_empty(self):
        """Test parsing empty score data."""
        score_data = {}
        score = FootballDataParser.parse_score(score_data)
        assert isinstance(score, Score)
        assert score.home == 0
        assert score.away == 0

    def test_parse_score_none_values(self):
        """Test parsing score data with None values."""
        score_data = {"fullTime": {"home": None, "away": None}}
        score = FootballDataParser.parse_score(score_data)
        assert isinstance(score, Score)
        assert score.home == 0
        assert score.away == 0

    def test_parse_match(self):
        """Test parsing match data."""
        match = FootballDataParser.parse_match(self.match_data)
        assert isinstance(match, Match)
        assert match.id == "123"
        assert isinstance(match.home_team, Team)
        assert match.home_team.id == "123"
        assert match.home_team.name == "Test Team"
        assert isinstance(match.away_team, Team)
        assert match.away_team.id == "456"
        assert match.away_team.name == "Away Team"
        assert isinstance(match.start_time, datetime.datetime)
        assert match.start_time.isoformat() == "2025-04-11T15:00:00+00:00"
        assert match.status == MatchStatus.IN_PLAY
        assert isinstance(match.score, Score)
        assert match.score.home == 2
        assert match.score.away == 1
        assert match.competition == "Test League"
        assert match.matchday == 5
        assert isinstance(match.last_updated, datetime.datetime)

    def test_parse_match_missing_id(self):
        """Test parsing match data with missing ID."""
        match_data = self.match_data.copy()
        del match_data["id"]
        with pytest.raises(ParserError):
            FootballDataParser.parse_match(match_data)

    def test_parse_match_missing_home_team(self):
        """Test parsing match data with missing home team."""
        match_data = self.match_data.copy()
        del match_data["homeTeam"]
        with pytest.raises(ParserError):
            FootballDataParser.parse_match(match_data)

    def test_parse_match_missing_away_team(self):
        """Test parsing match data with missing away team."""
        match_data = self.match_data.copy()
        del match_data["awayTeam"]
        with pytest.raises(ParserError):
            FootballDataParser.parse_match(match_data)

    def test_parse_match_missing_date(self):
        """Test parsing match data with missing date."""
        match_data = self.match_data.copy()
        del match_data["utcDate"]
        with pytest.raises(ParserError):
            FootballDataParser.parse_match(match_data)

    def test_parse_match_invalid_date(self):
        """Test parsing match data with invalid date."""
        match_data = self.match_data.copy()
        match_data["utcDate"] = "invalid-date"
        with pytest.raises(ParserError):
            FootballDataParser.parse_match(match_data)

    def test_parse_match_unknown_status(self):
        """Test parsing match data with unknown status."""
        match_data = self.match_data.copy()
        match_data["status"] = "UNKNOWN_STATUS"
        match = FootballDataParser.parse_match(match_data)
        assert match.status == MatchStatus.UNKNOWN

    def test_parse_matches(self):
        """Test parsing multiple matches."""
        matches = FootballDataParser.parse_matches(self.matches_data)
        assert isinstance(matches, list)
        assert len(matches) == 2
        assert all(isinstance(match, Match) for match in matches)
        assert matches[0].id == "123"
        assert matches[1].id == "456"

    def test_parse_matches_empty(self):
        """Test parsing empty matches data."""
        matches_data = {"matches": []}
        matches = FootballDataParser.parse_matches(matches_data)
        assert isinstance(matches, list)
        assert len(matches) == 0

    def test_parse_matches_invalid(self):
        """Test parsing invalid matches data."""
        matches_data = {"matches": "invalid"}
        matches = FootballDataParser.parse_matches(matches_data)
        assert isinstance(matches, list)
        assert len(matches) == 0

    def test_parse_matches_with_error(self):
        """Test parsing matches with one invalid match."""
        matches_data = {
            "matches": [
                self.match_data,
                {"id": 456},  # Invalid match data
            ]
        }
        matches = FootballDataParser.parse_matches(matches_data)
        assert isinstance(matches, list)
        assert len(matches) == 1
        assert matches[0].id == "123"

    def test_extract_events_match_start(self):
        """Test extracting match start event."""
        home_team = Team(id="123", name="Home Team")
        away_team = Team(id="456", name="Away Team")
        start_time = datetime.datetime.now()

        # Current match is live, no previous match
        current_match = Match(
            id="123",
            home_team=home_team,
            away_team=away_team,
            start_time=start_time,
            status=MatchStatus.IN_PLAY,
        )

        events = FootballDataParser.extract_events(current_match)
        assert len(events) == 1
        assert events[0].type == EventType.MATCH_START
        assert events[0].match_id == "123"

    def test_extract_events_status_change(self):
        """Test extracting events from status change."""
        home_team = Team(id="123", name="Home Team")
        away_team = Team(id="456", name="Away Team")
        start_time = datetime.datetime.now()

        # Previous match was scheduled, current match is live
        previous_match = Match(
            id="123",
            home_team=home_team,
            away_team=away_team,
            start_time=start_time,
            status=MatchStatus.SCHEDULED,
        )

        current_match = Match(
            id="123",
            home_team=home_team,
            away_team=away_team,
            start_time=start_time,
            status=MatchStatus.IN_PLAY,
        )

        events = FootballDataParser.extract_events(current_match, previous_match)
        assert len(events) == 1
        assert events[0].type == EventType.MATCH_START
        assert events[0].match_id == "123"

        # Previous match was live, current match is finished
        previous_match = Match(
            id="123",
            home_team=home_team,
            away_team=away_team,
            start_time=start_time,
            status=MatchStatus.IN_PLAY,
        )

        current_match = Match(
            id="123",
            home_team=home_team,
            away_team=away_team,
            start_time=start_time,
            status=MatchStatus.FINISHED,
        )

        events = FootballDataParser.extract_events(current_match, previous_match)
        assert len(events) == 1
        assert events[0].type == EventType.MATCH_END
        assert events[0].match_id == "123"

    def test_extract_events_goal(self):
        """Test extracting goal events."""
        home_team = Team(id="123", name="Home Team")
        away_team = Team(id="456", name="Away Team")
        start_time = datetime.datetime.now()

        # Previous match score: 0-0, current match score: 1-0
        previous_match = Match(
            id="123",
            home_team=home_team,
            away_team=away_team,
            start_time=start_time,
            status=MatchStatus.IN_PLAY,
            score=Score(home=0, away=0),
        )

        current_match = Match(
            id="123",
            home_team=home_team,
            away_team=away_team,
            start_time=start_time,
            status=MatchStatus.IN_PLAY,
            score=Score(home=1, away=0),
        )

        events = FootballDataParser.extract_events(current_match, previous_match)
        assert len(events) == 1
        assert events[0].type == EventType.GOAL
        assert events[0].match_id == "123"
        assert events[0].team_id == "123"  # Home team scored

        # Previous match score: 1-0, current match score: 1-1
        previous_match = Match(
            id="123",
            home_team=home_team,
            away_team=away_team,
            start_time=start_time,
            status=MatchStatus.IN_PLAY,
            score=Score(home=1, away=0),
        )

        current_match = Match(
            id="123",
            home_team=home_team,
            away_team=away_team,
            start_time=start_time,
            status=MatchStatus.IN_PLAY,
            score=Score(home=1, away=1),
        )

        events = FootballDataParser.extract_events(current_match, previous_match)
        assert len(events) == 1
        assert events[0].type == EventType.GOAL
        assert events[0].match_id == "123"
        assert events[0].team_id == "456"  # Away team scored

    def test_extract_events_multiple(self):
        """Test extracting multiple events."""
        home_team = Team(id="123", name="Home Team")
        away_team = Team(id="456", name="Away Team")
        start_time = datetime.datetime.now()

        # Previous match: scheduled, score 0-0
        # Current match: in play, score 1-0
        previous_match = Match(
            id="123",
            home_team=home_team,
            away_team=away_team,
            start_time=start_time,
            status=MatchStatus.SCHEDULED,
            score=Score(home=0, away=0),
        )

        current_match = Match(
            id="123",
            home_team=home_team,
            away_team=away_team,
            start_time=start_time,
            status=MatchStatus.IN_PLAY,
            score=Score(home=1, away=0),
        )

        events = FootballDataParser.extract_events(current_match, previous_match)
        assert len(events) == 2
        assert events[0].type == EventType.MATCH_START
        assert events[1].type == EventType.GOAL
        assert events[1].team_id == "123"  # Home team scored
