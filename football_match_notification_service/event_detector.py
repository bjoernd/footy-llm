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

    def __init__(self):
        """Initialize the event detector."""
        self._previous_states: Dict[str, Match] = {}
        self._detected_events: Set[str] = set()  # Track event IDs to avoid duplicates

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

        # Debug logging for match status
        if previous_match:
            logger.debug(
                f"Match status: previous={previous_match.status}, current={match.status}"
            )

        # Detect match start
        if self._is_match_start(match, previous_match):
            events.append(self._create_match_start_event(match))

        # Detect goals
        goal_events = self._detect_goals(match, previous_match)
        events.extend(goal_events)

        # Detect half-time
        if self._is_half_time(match, previous_match):
            half_time_event = self._create_half_time_event(match)
            events.append(half_time_event)
            logger.debug(f"Half-time event created: {half_time_event}")

        # Detect match end
        if self._is_match_end(match, previous_match):
            match_end_event = self._create_match_end_event(match)
            events.append(match_end_event)
            logger.debug(f"Match end event created: {match_end_event}")

        # Filter out duplicate events
        unique_events = self._filter_duplicate_events(events)

        logger.info(
            f"Found {len(events)} events, {len(unique_events)} unique for match {match.id}"
        )
        if events:
            logger.debug(f"Events before filtering: {events}")
            logger.debug(f"Events after filtering: {unique_events}")

        # Update previous state AFTER detecting events
        self._previous_states[match.id] = match.copy()

        return unique_events

    def _is_match_start(self, current: Match, previous: Optional[Match]) -> bool:
        """
        Determine if the match has just started.

        Args:
            current: Current match state
            previous: Previous match state

        Returns:
            True if the match has just started, False otherwise
        """
        # Match has started if:
        # 1. There was no previous state (first time we're seeing this match)
        # 2. Previous status was not in-play and current status is in-play
        # 3. Match is in first half and we're in the first few minutes

        if not previous:
            return True  # Always consider it a match start if we're seeing it for the first time

        return previous.status != "IN_PLAY" and current.status == "IN_PLAY"

    def _is_half_time(self, current: Match, previous: Optional[Match]) -> bool:
        """
        Determine if the match has just reached half-time.

        Args:
            current: Current match state
            previous: Previous match state

        Returns:
            True if the match has just reached half-time, False otherwise
        """
        if not previous:
            return False

        # Half-time is detected when:
        # 1. Previous status was in-play
        # 2. Current status is half-time

        # Debug logging
        logger.debug(
            f"Half-time check: previous={previous.status}, current={current.status}"
        )

        # Check if previous status was IN_PLAY
        prev_is_in_play = False
        if isinstance(previous.status, str):
            prev_is_in_play = previous.status == "IN_PLAY"
        else:
            prev_is_in_play = previous.status == MatchStatus.IN_PLAY

        # Check if current status is HALF_TIME
        curr_is_half_time = False
        if isinstance(current.status, str):
            curr_is_half_time = current.status == "HALF_TIME"
        else:
            curr_is_half_time = current.status == MatchStatus.HALF_TIME

        result = prev_is_in_play and curr_is_half_time

        # Debug logging
        logger.debug(f"Half-time detection result: {result}")

        return result

    def _is_match_end(self, current: Match, previous: Optional[Match]) -> bool:
        """
        Determine if the match has just ended.

        Args:
            current: Current match state
            previous: Previous match state

        Returns:
            True if the match has just ended, False otherwise
        """
        if not previous:
            return False

        # Match end is detected when:
        # 1. Previous status was in-play or in extra time
        # 2. Current status is finished

        # Convert string status to MatchStatus enum if needed
        prev_status = previous.status
        curr_status = current.status

        if isinstance(prev_status, str):
            prev_status = prev_status
        else:
            prev_status = prev_status.value

        if isinstance(curr_status, str):
            curr_status = curr_status
        else:
            curr_status = curr_status.value

        result = prev_status == "IN_PLAY" and curr_status == "FINISHED"

        # Debug logging
        logger.debug(
            f"Match end check: previous={prev_status}, current={curr_status}, result={result}"
        )

        return result

    def _detect_goals(self, current: Match, previous: Optional[Match]) -> List[Event]:
        """
        Detect goals by comparing current and previous match states.

        Args:
            current: Current match state
            previous: Previous match state

        Returns:
            A list of goal events
        """
        if not previous:
            # If this is the first time we're seeing this match and there are goals,
            # report them all as new events
            events = []
            home_goals = current.score.home
            away_goals = current.score.away

            for i in range(home_goals):
                events.append(self._create_goal_event(current, True, i + 1))

            for i in range(away_goals):
                events.append(self._create_goal_event(current, False, i + 1))

            return events

        events = []

        # Check for home team goals
        prev_home_goals = previous.score.home
        curr_home_goals = current.score.home

        if curr_home_goals > prev_home_goals:
            for i in range(prev_home_goals + 1, curr_home_goals + 1):
                events.append(self._create_goal_event(current, True, i))

        # Check for away team goals
        prev_away_goals = previous.score.away
        curr_away_goals = current.score.away

        if curr_away_goals > prev_away_goals:
            for i in range(prev_away_goals + 1, curr_away_goals + 1):
                events.append(self._create_goal_event(current, False, i))

        return events

    def _create_match_start_event(self, match: Match) -> Event:
        """
        Create a match start event.

        Args:
            match: The match that has started

        Returns:
            A match start event
        """
        event_id = f"{match.id}_start"
        return Event(
            id=event_id,
            match_id=match.id,
            type=EventType.MATCH_START,
            minute=0,
            team_id=None,
            player_name=None,
            description=f"Match started: {match.home_team.name} vs {match.away_team.name}",
        )

    def _create_half_time_event(self, match: Match) -> Event:
        """
        Create a half-time event.

        Args:
            match: The match that has reached half-time

        Returns:
            A half-time event
        """
        event_id = f"{match.id}_half_time"
        score_str = f"{match.score.home}-{match.score.away}"
        return Event(
            id=event_id,
            match_id=match.id,
            type=EventType.HALF_TIME,
            minute=45,
            team_id=None,
            player_name=None,
            description=f"Half-time: {match.home_team.name} {score_str} {match.away_team.name}",
        )

    def _create_match_end_event(self, match: Match) -> Event:
        """
        Create a match end event.

        Args:
            match: The match that has ended

        Returns:
            A match end event
        """
        event_id = f"{match.id}_end"
        score_str = f"{match.score.home}-{match.score.away}"
        return Event(
            id=event_id,
            match_id=match.id,
            type=EventType.MATCH_END,
            minute=90,  # Approximate, could be more with extra time
            team_id=None,
            player_name=None,
            description=f"Match ended: {match.home_team.name} {score_str} {match.away_team.name}",
        )

    def _create_goal_event(
        self, match: Match, is_home_team: bool, goal_number: int
    ) -> Event:
        """
        Create a goal event.

        Args:
            match: The match in which the goal was scored
            is_home_team: True if the goal was scored by the home team, False otherwise
            goal_number: The goal number for the scoring team

        Returns:
            A goal event
        """
        team = match.home_team if is_home_team else match.away_team
        opponent = match.away_team if is_home_team else match.home_team

        event_id = f"{match.id}_{team.id}_goal_{goal_number}"
        score_str = f"{match.score.home}-{match.score.away}"

        return Event(
            id=event_id,
            match_id=match.id,
            type=EventType.GOAL,
            minute=match.minute,
            team_id=team.id,
            player_name=None,  # We don't have this information from the API
            description=f"GOAL! {team.name} {score_str} {opponent.name}",
        )

    def _filter_duplicate_events(self, events: List[Event]) -> List[Event]:
        """
        Filter out duplicate events that have already been detected.

        Args:
            events: List of detected events

        Returns:
            List of unique events that haven't been detected before
        """
        unique_events = []

        for event in events:
            # Debug logging for each event being processed
            logger.debug(f"Processing event: {event.id}, type: {event.type}")

            if event.id not in self._detected_events:
                logger.debug(f"Adding new event: {event.id}")
                self._detected_events.add(event.id)
                unique_events.append(event)
            else:
                logger.debug(f"Filtering out duplicate event: {event.id}")

        # Debug logging
        if len(unique_events) != len(events):
            logger.debug(
                f"Filtered out {len(events) - len(unique_events)} duplicate events"
            )
            logger.debug(f"Detected events set: {self._detected_events}")

        # Add additional debug logging to help diagnose issues
        logger.debug(f"Returning {len(unique_events)} unique events: {unique_events}")

        return unique_events

    def reset(self) -> None:
        """Reset the event detector state."""
        self._previous_states.clear()
        self._detected_events.clear()
        logger.debug("Event detector state reset")
