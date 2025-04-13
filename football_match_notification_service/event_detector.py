"""
Event detector module for the Football Match Notification Service.

This module is responsible for detecting events in football matches by comparing
the current match state with the previous state.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple

from football_match_notification_service.models import (
    Event,
    Match,
    EventType,
    MatchStatus,
)
from football_match_notification_service.logger import get_logger
from football_match_notification_service.api_client import APIFootballClient
from football_match_notification_service.parsers import APIFootballParser

logger = get_logger(__name__)


class EventDetector:
    """
    Detects events in football matches by comparing current and previous match states.

    This class is responsible for identifying key events such as:
    - Match start
    - Goals
    - Half-time
    - Match end
    - Red/yellow cards
    - Substitutions
    """

    def __init__(self, api_client: APIFootballClient):
        """
        Initialize the event detector.
        
        Args:
            api_client: API client for fetching event data
        """
        self._previous_states: Dict[str, Match] = {}
        self._detected_events: Set[str] = set()  # Track event IDs to avoid duplicates
        self.api_client = api_client
        self.parser = APIFootballParser()

    def detect_events(self, match: Match) -> List[Event]:
        """
        Detect events by comparing the current match state with the previous state.

        Args:
            match: The current match state

        Returns:
            A list of detected events
        """
        events = []
        
        # Get previous state if available
        previous_match = self._previous_states.get(match.id)
        
        # Detect match start
        if self._is_match_start(previous_match, match):
            event = Event.create_match_start_event(match)
            if self._add_event(event):
                events.append(event)
                logger.match_start(
                    f"Match started: {match.home_team.name} vs {match.away_team.name}",
                    extra={"match_id": match.id}
                )
        
        # Detect half-time
        if self._is_half_time(previous_match, match):
            event = Event.create_half_time_event(match)
            if self._add_event(event):
                events.append(event)
                logger.match_event(
                    f"Half-time: {match.home_team.name} {match.score.home}-{match.score.away} {match.away_team.name}",
                    extra={"match_id": match.id}
                )
        
        # Detect match end
        if self._is_match_end(previous_match, match):
            event = Event.create_match_end_event(match)
            if self._add_event(event):
                events.append(event)
                logger.match_end(
                    f"Match ended: {match.home_team.name} {match.score.home}-{match.score.away} {match.away_team.name}",
                    extra={"match_id": match.id}
                )
        
        # Detect score changes
        if previous_match and self._is_score_changed(previous_match, match):
            # Fetch detailed events from API to get goal information
            api_events = self._fetch_match_events(match.id)
            
            # Filter for goal events that we haven't seen before
            for event in api_events:
                if event.type == EventType.GOAL and self._add_event(event):
                    events.append(event)
                    team_name = match.home_team.name if event.team_id == match.home_team.id else match.away_team.name
                    logger.goal(
                        f"Goal! {team_name} - {event.player_name or 'Unknown player'} ({event.minute}')",
                        extra={"match_id": match.id, "team_id": event.team_id}
                    )
        
        # Update previous state
        self._previous_states[match.id] = match
        
        return events

    def _is_match_start(self, previous: Optional[Match], current: Match) -> bool:
        """
        Determine if a match has just started.
        
        Args:
            previous: Previous match state
            current: Current match state
            
        Returns:
            True if the match has just started, False otherwise
        """
        # Match has started if:
        # 1. There was no previous state or previous state was not IN_PLAY
        # 2. Current state is IN_PLAY
        return (
            (previous is None or previous.status not in [MatchStatus.IN_PLAY, MatchStatus.HALF_TIME, MatchStatus.PAUSED]) and
            current.status == MatchStatus.IN_PLAY
        )

    def _is_half_time(self, previous: Optional[Match], current: Match) -> bool:
        """
        Determine if a match has reached half-time.
        
        Args:
            previous: Previous match state
            current: Current match state
            
        Returns:
            True if the match has reached half-time, False otherwise
        """
        # Match is at half-time if:
        # 1. Previous state was IN_PLAY
        # 2. Current state is HALF_TIME
        return (
            previous is not None and
            previous.status == MatchStatus.IN_PLAY and
            current.status == MatchStatus.HALF_TIME
        )

    def _is_match_end(self, previous: Optional[Match], current: Match) -> bool:
        """
        Determine if a match has ended.
        
        Args:
            previous: Previous match state
            current: Current match state
            
        Returns:
            True if the match has ended, False otherwise
        """
        # Match has ended if:
        # 1. Previous state was IN_PLAY, HALF_TIME, or PAUSED
        # 2. Current state is FINISHED
        return (
            previous is not None and
            previous.status in [MatchStatus.IN_PLAY, MatchStatus.HALF_TIME, MatchStatus.PAUSED] and
            current.status == MatchStatus.FINISHED
        )

    def _is_score_changed(self, previous: Match, current: Match) -> bool:
        """
        Determine if the score has changed.
        
        Args:
            previous: Previous match state
            current: Current match state
            
        Returns:
            True if the score has changed, False otherwise
        """
        return (
            previous.score.home != current.score.home or
            previous.score.away != current.score.away
        )

    def _add_event(self, event: Event) -> bool:
        """
        Add an event to the detected events set if it's new.
        
        Args:
            event: Event to add
            
        Returns:
            True if the event was added, False if it was already detected
        """
        if event.id in self._detected_events:
            return False
            
        self._detected_events.add(event.id)
        return True

    def _fetch_match_events(self, match_id: str) -> List[Event]:
        """
        Fetch events for a specific match from the API.
        
        Args:
            match_id: Match ID
            
        Returns:
            List of events for the match
        """
        try:
            response = self.api_client.get_fixtures_events(match_id)
            return self.parser.parse_events(response, match_id)
        except Exception as e:
            logger.error(f"Error fetching events for match {match_id}: {e}")
            return []

    def clear_match_state(self, match_id: str) -> None:
        """
        Clear the state for a specific match.
        
        Args:
            match_id: Match ID to clear
        """
        if match_id in self._previous_states:
            del self._previous_states[match_id]
            
        # Remove events for this match from detected events
        self._detected_events = {
            event_id for event_id in self._detected_events
            if not event_id.startswith(f"{match_id}_")
        }

    def clear_old_matches(self) -> None:
        """
        Clear state for all finished matches.
        """
        finished_matches = [
            match_id for match_id, match in self._previous_states.items()
            if match.status in [MatchStatus.FINISHED, MatchStatus.CANCELLED, MatchStatus.POSTPONED]
        ]
        
        for match_id in finished_matches:
            self.clear_match_state(match_id)
