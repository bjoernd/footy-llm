"""
Scheduler module for Football Match Notification Service.

This module provides a flexible scheduling framework for running tasks at specified
intervals or at specific times. It supports:
- Adding and removing scheduled tasks
- Running tasks at regular intervals
- Running tasks at specific times
- Error handling for task execution
- Dynamic scheduling based on match status
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional, Union, Any

from football_match_notification_service.logger import get_logger

logger = get_logger(__name__)


class Task:
    """Represents a scheduled task with execution parameters."""

    def __init__(
        self,
        name: str,
        callback: Callable,
        interval: Optional[int] = None,
        run_at: Optional[Union[datetime, List[datetime]]] = None,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        run_once: bool = False,
    ):
        """
        Initialize a scheduled task.

        Args:
            name: Unique name for the task
            callback: Function to call when the task is executed
            interval: Time in seconds between executions (for interval-based tasks)
            run_at: Specific time(s) to run the task (for time-based tasks)
            args: Positional arguments to pass to the callback
            kwargs: Keyword arguments to pass to the callback
            run_once: If True, the task will be removed after execution
        """
        self.name = name
        self.callback = callback
        self.interval = interval
        self.run_at = run_at if isinstance(run_at, list) or run_at is None else [run_at]
        self.args = args or []
        self.kwargs = kwargs or {}
        self.run_once = run_once
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self._calculate_next_run()

    def _calculate_next_run(self) -> None:
        """Calculate the next execution time for this task."""
        now = datetime.now()

        if self.interval is not None:
            # For interval-based tasks
            if self.last_run is None:
                self.next_run = now
            else:
                self.next_run = self.last_run + timedelta(seconds=self.interval)
        elif self.run_at:
            # For time-based tasks
            future_times = [t for t in self.run_at if t > now]
            if future_times:
                self.next_run = min(future_times)
            else:
                # All specified times are in the past
                self.next_run = None
        else:
            # Neither interval nor run_at specified
            self.next_run = None

    def should_run(self) -> bool:
        """Check if the task should be executed now."""
        if self.next_run is None:
            return False
        return datetime.now() >= self.next_run

    def execute(self) -> None:
        """Execute the task and update execution timestamps."""
        try:
            logger.debug(f"Executing task: {self.name}")
            self.callback(*self.args, **self.kwargs)
            self.last_run = datetime.now()
            self._calculate_next_run()
        except Exception as e:
            logger.error(f"Error executing task {self.name}: {str(e)}")
            # Still update last_run and calculate next_run even if there was an error
            self.last_run = datetime.now()
            self._calculate_next_run()


class Scheduler:
    """
    Scheduler for managing and executing tasks at specified intervals or times.
    """

    def __init__(self, check_interval: int = 1):
        """
        Initialize the scheduler.

        Args:
            check_interval: How often (in seconds) to check for tasks to run
        """
        self.tasks: Dict[str, Task] = {}
        self.check_interval = check_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        logger.info("Scheduler initialized")

    def add_task(
        self,
        name: str,
        callback: Callable,
        interval: Optional[int] = None,
        run_at: Optional[Union[datetime, List[datetime]]] = None,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        run_once: bool = False,
    ) -> None:
        """
        Add a task to the scheduler.

        Args:
            name: Unique name for the task
            callback: Function to call when the task is executed
            interval: Time in seconds between executions (for interval-based tasks)
            run_at: Specific time(s) to run the task (for time-based tasks)
            args: Positional arguments to pass to the callback
            kwargs: Keyword arguments to pass to the callback
            run_once: If True, the task will be removed after execution

        Raises:
            ValueError: If neither interval nor run_at is specified
            ValueError: If a task with the same name already exists
        """
        if interval is None and run_at is None:
            raise ValueError("Either interval or run_at must be specified")

        if name in self.tasks:
            raise ValueError(f"Task with name '{name}' already exists")

        task = Task(
            name=name,
            callback=callback,
            interval=interval,
            run_at=run_at,
            args=args,
            kwargs=kwargs,
            run_once=run_once,
        )
        self.tasks[name] = task
        logger.info(f"Added task: {name}")

    def remove_task(self, name: str) -> bool:
        """
        Remove a task from the scheduler.

        Args:
            name: Name of the task to remove

        Returns:
            True if the task was removed, False if it didn't exist
        """
        if name in self.tasks:
            del self.tasks[name]
            logger.info(f"Removed task: {name}")
            return True
        return False

    def get_task(self, name: str) -> Optional[Task]:
        """
        Get a task by name.

        Args:
            name: Name of the task to get

        Returns:
            The task if found, None otherwise
        """
        return self.tasks.get(name)

    def list_tasks(self) -> List[str]:
        """
        Get a list of all task names.

        Returns:
            List of task names
        """
        return list(self.tasks.keys())

    def start(self) -> None:
        """Start the scheduler in a separate thread."""
        if self._running:
            logger.warning("Scheduler is already running")
            return

        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Scheduler started")

    def stop(self) -> None:
        """Stop the scheduler."""
        if not self._running:
            logger.warning("Scheduler is not running")
            return

        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5.0)
        self._running = False
        logger.info("Scheduler stopped")

    def _run(self) -> None:
        """Main scheduler loop that checks and executes tasks."""
        while not self._stop_event.is_set():
            self._check_tasks()
            # Sleep for the check interval, but allow interruption
            self._stop_event.wait(self.check_interval)

    def _check_tasks(self) -> None:
        """Check all tasks and execute those that are due."""
        tasks_to_remove = []

        for name, task in self.tasks.items():
            if task.should_run():
                task.execute()
                if task.run_once:
                    tasks_to_remove.append(name)

        # Remove one-time tasks that have been executed
        for name in tasks_to_remove:
            self.remove_task(name)

    def is_running(self) -> bool:
        """
        Check if the scheduler is currently running.

        Returns:
            True if the scheduler is running, False otherwise
        """
        return self._running


# Singleton instance
_scheduler_instance: Optional[Scheduler] = None


def get_scheduler(check_interval: int = 1) -> Scheduler:
    """
    Get the singleton scheduler instance.

    Args:
        check_interval: How often (in seconds) to check for tasks to run

    Returns:
        The scheduler instance
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = Scheduler(check_interval=check_interval)
    return _scheduler_instance
