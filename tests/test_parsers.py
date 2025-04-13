"""
Tests for the parsers module.
"""

import datetime
import json
from unittest.mock import MagicMock, patch

import pytest

from football_match_notification_service.models import (
    Event,
    EventType,
    Match,
    MatchStatus,
    Score,
    Team,
)
from football_match_notification_service.parsers import (
    APIFootballParser,
    ParserError,
)


class TestAPIFootballParser:
    """Tests for the API-Football parser."""

    def test_parse_team(self):
        """Test parsing a team from API-Football data."""
        team_data = {
            "id": 123,
            "name": "Test Team",
            "code": "TEST",
            "logo": "http://example.com/logo.png",
            "country": "Test Country"
        }
        
        team = APIFootballParser.parse_team(team_data)
        
        assert team.id == "123"
        assert team.name == "Test Team"
        assert team.short_name == "TEST"
        assert team.logo_url == "http://example.com/logo.png"
        assert team.country == "Test Country"

    def test_parse_team_error(self):
        """Test error handling when parsing a team."""
        with patch("football_match_notification_service.models.Team.from_api_football", side_effect=Exception("Test error")):
            with pytest.raises(ParserError, match="Failed to parse team data"):
                APIFootballParser.parse_team({"id": 123})

    def test_parse_match(self):
        """Test parsing a match from API-Football data."""
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
        
        match = APIFootballParser.parse_match(match_data)
        
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

    def test_parse_match_error(self):
        """Test error handling when parsing a match."""
        with patch("football_match_notification_service.models.Match.from_api_football", side_effect=Exception("Test error")):
            with pytest.raises(ParserError, match="Failed to parse match data"):
                APIFootballParser.parse_match({"fixture": {"id": 789}})

    def test_parse_matches(self):
        """Test parsing multiple matches from API-Football data."""
        response_data = {
            "response": [
                {
                    "fixture": {
                        "id": 789,
                        "date": "2023-01-01T15:00:00Z",
                        "status": {
                            "short": "FT"
                        }
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
                        "name": "Test League"
                    }
                },
                {
                    "fixture": {
                        "id": 790,
                        "date": "2023-01-02T15:00:00Z",
                        "status": {
                            "short": "NS"
                        }
                    },
                    "teams": {
                        "home": {
                            "id": 123,
                            "name": "Home Team"
                        },
                        "away": {
                            "id": 457,
                            "name": "Another Away Team"
                        }
                    },
                    "goals": {
                        "home": 0,
                        "away": 0
                    },
                    "league": {
                        "name": "Test League"
                    }
                }
            ]
        }
        
        matches = APIFootballParser.parse_matches(response_data)
        
        assert len(matches) == 2
        assert matches[0].id == "789"
        assert matches[0].status == MatchStatus.FINISHED
        assert matches[1].id == "790"
        assert matches[1].status == MatchStatus.SCHEDULED

    def test_parse_matches_with_invalid_item(self):
        """Test parsing matches with an invalid item in the response."""
        response_data = {
            "response": [
                {
                    "fixture": {
                        "id": 789,
                        "date": "2023-01-01T15:00:00Z",
                        "status": {
                            "short": "FT"
                        }
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
                        "name": "Test League"
                    }
                },
                # Invalid match data
                {
                    "fixture": "invalid"
                }
            ]
        }
        
        # Should not raise an exception, but skip the invalid item
        matches = APIFootballParser.parse_matches(response_data)
        
        assert len(matches) == 1
        assert matches[0].id == "789"

    def test_parse_matches_invalid_response(self):
        """Test error handling when parsing matches with invalid response format."""
        response_data = {
            "response": "not a list"
        }
        
        with pytest.raises(ParserError, match="Invalid response format"):
            APIFootballParser.parse_matches(response_data)

    def test_parse_event(self):
        """Test parsing an event from API-Football data."""
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
        
        event = APIFootballParser.parse_event(event_data, "123")
        
        assert event.id == "123_45_GOAL_456"
        assert event.match_id == "123"
        assert event.type == EventType.GOAL
        assert event.minute == 45
        assert event.team_id == "456"
        assert event.player_name == "Test Player"
        assert event.description == "Test Player - Normal Goal - Great shot"

    def test_parse_event_error(self):
        """Test error handling when parsing an event."""
        with patch("football_match_notification_service.models.Event.from_api_football", side_effect=Exception("Test error")):
            with pytest.raises(ParserError, match="Failed to parse event data"):
                APIFootballParser.parse_event({"time": {"elapsed": 45}}, "123")

    def test_parse_events(self):
        """Test parsing multiple events from API-Football data."""
        response_data = {
            "response": [
                {
                    "time": {
                        "elapsed": 45
                    },
                    "type": "Goal",
                    "detail": "Normal Goal",
                    "team": {
                        "id": 456
                    },
                    "player": {
                        "name": "Test Player"
                    }
                },
                {
                    "time": {
                        "elapsed": 60
                    },
                    "type": "Card",
                    "detail": "Yellow Card",
                    "team": {
                        "id": 123
                    },
                    "player": {
                        "name": "Another Player"
                    }
                }
            ]
        }
        
        events = APIFootballParser.parse_events(response_data, "789")
        
        assert len(events) == 2
        assert events[0].type == EventType.GOAL
        assert events[0].minute == 45
        assert events[1].type == EventType.YELLOW_CARD
        assert events[1].minute == 60

    def test_parse_events_with_invalid_item(self):
        """Test parsing events with an invalid item in the response."""
        response_data = {
            "response": [
                {
                    "time": {
                        "elapsed": 45
                    },
                    "type": "Goal",
                    "detail": "Normal Goal",
                    "team": {
                        "id": 456
                    },
                    "player": {
                        "name": "Test Player"
                    }
                },
                # Invalid event data
                {
                    "time": "invalid"
                }
            ]
        }
        
        # Should not raise an exception, but skip the invalid item
        events = APIFootballParser.parse_events(response_data, "789")
        
        assert len(events) == 1
        assert events[0].type == EventType.GOAL

    def test_parse_events_invalid_response(self):
        """Test error handling when parsing events with invalid response format."""
        response_data = {
            "response": "not a list"
        }
        
        with pytest.raises(ParserError, match="Invalid response format"):
            APIFootballParser.parse_events(response_data, "789")

    def test_normalize_date(self):
        """Test normalizing date strings."""
        # ISO format
        assert APIFootballParser.normalize_date("2023-01-01T15:00:00Z") == "2023-01-01"
        
        # YYYY-MM-DD
        assert APIFootballParser.normalize_date("2023-01-01") == "2023-01-01"
        
        # DD/MM/YYYY - we're assuming international format
        assert APIFootballParser.normalize_date("15/01/2023") == "2023-01-15"
        
        # Test with day > 12 to ensure it's treated as DD/MM format
        assert APIFootballParser.normalize_date("15/02/2023") == "2023-02-15"
        
        # Test with explicit formats
        assert APIFootballParser.normalize_date("2023-02-01") == "2023-02-01"  # YYYY-MM-DD
        assert APIFootballParser.normalize_date("15-02-2023") == "2023-02-15"  # DD-MM-YYYY

    def test_normalize_date_error(self):
        """Test error handling when normalizing an invalid date string."""
        with pytest.raises(ValueError, match="Could not parse date string"):
            APIFootballParser.normalize_date("invalid date")

    def test_extract_team_ids(self):
        """Test extracting team IDs from API-Football data."""
        response_data = {
            "response": [
                {
                    "team": {
                        "id": 123,
                        "name": "Team 1"
                    }
                },
                {
                    "team": {
                        "id": 456,
                        "name": "Team 2"
                    }
                },
                {
                    "team": {
                        "id": 789,
                        "name": "Team 3"
                    }
                }
            ]
        }
        
        team_ids = APIFootballParser.extract_team_ids(response_data)
        
        assert team_ids == ["123", "456", "789"]

    def test_extract_team_ids_with_missing_id(self):
        """Test extracting team IDs with a missing ID in the response."""
        response_data = {
            "response": [
                {
                    "team": {
                        "id": 123,
                        "name": "Team 1"
                    }
                },
                {
                    "team": {
                        "name": "Team 2"  # Missing ID
                    }
                },
                {
                    "team": {
                        "id": 789,
                        "name": "Team 3"
                    }
                }
            ]
        }
        
        team_ids = APIFootballParser.extract_team_ids(response_data)
        
        assert team_ids == ["123", "789"]

    def test_extract_team_ids_invalid_response(self):
        """Test error handling when extracting team IDs with invalid response format."""
        response_data = {
            "response": "not a list"
        }
        
        with pytest.raises(ParserError, match="Invalid response format"):
            APIFootballParser.extract_team_ids(response_data)
