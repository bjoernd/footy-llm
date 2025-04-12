"""
Tests for the scheduler module.
"""

import time
import threading
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from football_match_notification_service.scheduler import (
    Task,
    Scheduler,
    get_scheduler,
)


class TestTask:
    """Tests for the Task class."""

    def test_init(self):
        """Test Task initialization."""
        callback = MagicMock()
        task = Task(
            name="test_task",
            callback=callback,
            interval=60,
            args=[1, 2],
            kwargs={"a": "b"},
        )

        assert task.name == "test_task"
        assert task.callback == callback
        assert task.interval == 60
        assert task.args == [1, 2]
        assert task.kwargs == {"a": "b"}
        assert task.run_once is False
        assert task.last_run is None
        assert task.next_run is not None

    def test_init_with_run_at(self):
        """Test Task initialization with run_at parameter."""
        callback = MagicMock()
        future_time = datetime.now() + timedelta(hours=1)
        task = Task(
            name="test_task",
            callback=callback,
            run_at=future_time,
        )

        assert task.name == "test_task"
        assert task.callback == callback
        assert task.interval is None
        assert task.run_at == [future_time]
        assert task.last_run is None
        assert task.next_run == future_time

    def test_init_with_run_at_list(self):
        """Test Task initialization with run_at as a list."""
        callback = MagicMock()
        future_time1 = datetime.now() + timedelta(hours=1)
        future_time2 = datetime.now() + timedelta(hours=2)
        task = Task(
            name="test_task",
            callback=callback,
            run_at=[future_time1, future_time2],
        )

        assert task.name == "test_task"
        assert task.callback == callback
        assert task.interval is None
        assert task.run_at == [future_time1, future_time2]
        assert task.last_run is None
        assert task.next_run == future_time1  # Should pick the earliest time

    def test_should_run_interval(self):
        """Test should_run for interval-based tasks."""
        callback = MagicMock()
        # Create a task that should run immediately
        task = Task(
            name="test_task",
            callback=callback,
            interval=0,
        )

        assert task.should_run() is True

        # Create a task with a future next_run
        task = Task(
            name="test_task",
            callback=callback,
            interval=3600,  # 1 hour
        )
        task.next_run = datetime.now() + timedelta(minutes=30)
        assert task.should_run() is False

    def test_should_run_time_based(self):
        """Test should_run for time-based tasks."""
        callback = MagicMock()
        # Create a task with a past run_at time
        past_time = datetime.now() - timedelta(hours=1)
        task = Task(
            name="test_task",
            callback=callback,
            run_at=past_time,
        )

        # Force next_run to be in the past for testing
        task.next_run = past_time

        assert task.should_run() is True

        # Create a task with a future run_at time
        future_time = datetime.now() + timedelta(hours=1)
        task = Task(
            name="test_task",
            callback=callback,
            run_at=future_time,
        )

        assert task.should_run() is False

    def test_execute(self):
        """Test task execution."""
        callback = MagicMock()
        task = Task(
            name="test_task",
            callback=callback,
            interval=60,
            args=[1, 2],
            kwargs={"a": "b"},
        )

        task.execute()
        callback.assert_called_once_with(1, 2, a="b")
        assert task.last_run is not None
        assert task.next_run > task.last_run

    def test_execute_with_exception(self):
        """Test task execution with an exception."""
        callback = MagicMock(side_effect=ValueError("Test error"))
        task = Task(
            name="test_task",
            callback=callback,
        )

        # Should not raise an exception
        task.execute()
        callback.assert_called_once()
        assert task.last_run is not None

    def test_calculate_next_run_interval(self):
        """Test _calculate_next_run for interval-based tasks."""
        callback = MagicMock()
        task = Task(
            name="test_task",
            callback=callback,
            interval=60,
        )

        # Initial next_run should be now
        assert (datetime.now() - task.next_run).total_seconds() < 1

        # After execution, next_run should be interval seconds after last_run
        task.execute()
        expected_next_run = task.last_run + timedelta(seconds=60)
        assert abs((expected_next_run - task.next_run).total_seconds()) < 1

    def test_calculate_next_run_time_based(self):
        """Test _calculate_next_run for time-based tasks."""
        callback = MagicMock()
        future_time1 = datetime.now() + timedelta(hours=1)
        future_time2 = datetime.now() + timedelta(minutes=30)
        task = Task(
            name="test_task",
            callback=callback,
            run_at=[future_time1, future_time2],
        )

        # Should pick the earliest future time
        assert task.next_run == future_time2

        # After all times have passed, next_run should be None
        task.run_at = [datetime.now() - timedelta(hours=1)]
        task._calculate_next_run()
        assert task.next_run is None


class TestScheduler:
    """Tests for the Scheduler class."""

    def test_init(self):
        """Test Scheduler initialization."""
        scheduler = Scheduler(check_interval=5)
        assert scheduler.check_interval == 5
        assert scheduler._running is False
        assert scheduler._thread is None
        assert len(scheduler.tasks) == 0

    def test_add_task(self):
        """Test adding a task to the scheduler."""
        scheduler = Scheduler()
        callback = MagicMock()

        scheduler.add_task(
            name="test_task",
            callback=callback,
            interval=60,
        )

        assert "test_task" in scheduler.tasks
        assert scheduler.tasks["test_task"].callback == callback
        assert scheduler.tasks["test_task"].interval == 60

    def test_add_task_with_invalid_params(self):
        """Test adding a task with invalid parameters."""
        scheduler = Scheduler()
        callback = MagicMock()

        # Neither interval nor run_at specified
        with pytest.raises(ValueError):
            scheduler.add_task(
                name="test_task",
                callback=callback,
            )

        # Task with same name already exists
        scheduler.add_task(
            name="test_task",
            callback=callback,
            interval=60,
        )
        with pytest.raises(ValueError):
            scheduler.add_task(
                name="test_task",
                callback=MagicMock(),
                interval=30,
            )

    def test_remove_task(self):
        """Test removing a task from the scheduler."""
        scheduler = Scheduler()
        callback = MagicMock()

        scheduler.add_task(
            name="test_task",
            callback=callback,
            interval=60,
        )

        assert scheduler.remove_task("test_task") is True
        assert "test_task" not in scheduler.tasks

        # Removing non-existent task
        assert scheduler.remove_task("non_existent") is False

    def test_get_task(self):
        """Test getting a task by name."""
        scheduler = Scheduler()
        callback = MagicMock()

        scheduler.add_task(
            name="test_task",
            callback=callback,
            interval=60,
        )

        task = scheduler.get_task("test_task")
        assert task is not None
        assert task.name == "test_task"
        assert task.callback == callback

        # Getting non-existent task
        assert scheduler.get_task("non_existent") is None

    def test_list_tasks(self):
        """Test listing all tasks."""
        scheduler = Scheduler()
        callback = MagicMock()

        scheduler.add_task(
            name="test_task1",
            callback=callback,
            interval=60,
        )
        scheduler.add_task(
            name="test_task2",
            callback=callback,
            interval=30,
        )

        task_list = scheduler.list_tasks()
        assert len(task_list) == 2
        assert "test_task1" in task_list
        assert "test_task2" in task_list

    def test_start_stop(self):
        """Test starting and stopping the scheduler."""
        scheduler = Scheduler()

        # Start the scheduler
        scheduler.start()
        assert scheduler._running is True
        assert scheduler._thread is not None
        assert scheduler._thread.is_alive() is True

        # Try starting again
        scheduler.start()  # Should log a warning but not crash

        # Stop the scheduler
        scheduler.stop()
        assert scheduler._running is False

        # Give the thread time to stop
        time.sleep(0.1)
        assert scheduler._thread.is_alive() is False

        # Try stopping again
        scheduler.stop()  # Should log a warning but not crash

    def test_is_running(self):
        """Test is_running method."""
        scheduler = Scheduler()
        assert scheduler.is_running() is False

        scheduler.start()
        assert scheduler.is_running() is True

        scheduler.stop()
        assert scheduler.is_running() is False

    @patch("football_match_notification_service.scheduler.Task")
    def test_check_tasks(self, mock_task_class):
        """Test _check_tasks method."""
        scheduler = Scheduler()
        callback = MagicMock()

        # Create mock tasks
        task1 = MagicMock()
        task1.name = "task1"
        task1.should_run.return_value = True
        task1.run_once = False

        task2 = MagicMock()
        task2.name = "task2"
        task2.should_run.return_value = True
        task2.run_once = True

        task3 = MagicMock()
        task3.name = "task3"
        task3.should_run.return_value = False

        # Add tasks to scheduler
        scheduler.tasks = {
            "task1": task1,
            "task2": task2,
            "task3": task3,
        }

        # Run _check_tasks
        scheduler._check_tasks()

        # Verify task execution
        task1.should_run.assert_called_once()
        task1.execute.assert_called_once()
        assert "task1" in scheduler.tasks  # Not removed

        task2.should_run.assert_called_once()
        task2.execute.assert_called_once()
        assert "task2" not in scheduler.tasks  # Removed because run_once=True

        task3.should_run.assert_called_once()
        task3.execute.assert_not_called()
        assert "task3" in scheduler.tasks  # Not removed

    def test_run_with_real_execution(self):
        """Test the scheduler with real task execution."""
        scheduler = Scheduler(check_interval=0.1)
        counter = {"count": 0}

        def increment_counter():
            counter["count"] += 1

        # Add a task that runs immediately and every 0.2 seconds
        scheduler.add_task(
            name="increment",
            callback=increment_counter,
            interval=0.2,
        )

        # Start the scheduler
        scheduler.start()

        # Let it run for a bit
        time.sleep(0.5)

        # Stop the scheduler
        scheduler.stop()

        # Check that the counter was incremented at least twice
        # (once immediately and at least once more after 0.2 seconds)
        assert counter["count"] >= 2


class TestGetScheduler:
    """Tests for the get_scheduler function."""

    def test_get_scheduler(self):
        """Test get_scheduler returns a singleton instance."""
        scheduler1 = get_scheduler()
        scheduler2 = get_scheduler()

        assert scheduler1 is scheduler2
        assert isinstance(scheduler1, Scheduler)

        # Test with different check_interval
        scheduler3 = get_scheduler(check_interval=5)
        assert scheduler3 is scheduler1  # Still the same instance
        assert scheduler3.check_interval != 5  # Parameter ignored after first call
