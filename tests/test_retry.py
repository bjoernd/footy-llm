"""
Tests for the retry mechanism.
"""

import time
import unittest
from unittest.mock import MagicMock, patch

import pytest
import requests

from football_match_notification_service.api_client import (
    APIClientError,
    RateLimitError,
)
from football_match_notification_service.retry import (
    CircuitBreaker,
    CircuitBreakerError,
    get_circuit_breaker,
    retry,
)


class TestCircuitBreaker(unittest.TestCase):
    """Test cases for the circuit breaker."""

    def setUp(self):
        """Set up test fixtures."""
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1)

    def test_initial_state(self):
        """Test initial state of circuit breaker."""
        assert self.circuit_breaker.state == "CLOSED"
        assert self.circuit_breaker.failure_count == 0
        assert self.circuit_breaker.allow_request() is True

    def test_record_success(self):
        """Test recording a successful request."""
        # Record some failures first
        self.circuit_breaker.record_failure()
        self.circuit_breaker.record_failure()
        assert self.circuit_breaker.failure_count == 2

        # Record success
        self.circuit_breaker.record_success()
        assert self.circuit_breaker.state == "CLOSED"
        assert self.circuit_breaker.failure_count == 0

    def test_record_failure_below_threshold(self):
        """Test recording failures below threshold."""
        self.circuit_breaker.record_failure()
        self.circuit_breaker.record_failure()
        assert self.circuit_breaker.state == "CLOSED"
        assert self.circuit_breaker.failure_count == 2
        assert self.circuit_breaker.allow_request() is True

    def test_record_failure_above_threshold(self):
        """Test recording failures above threshold."""
        self.circuit_breaker.record_failure()
        self.circuit_breaker.record_failure()
        self.circuit_breaker.record_failure()
        assert self.circuit_breaker.state == "OPEN"
        assert self.circuit_breaker.failure_count == 3
        assert self.circuit_breaker.allow_request() is False

    def test_recovery_timeout(self):
        """Test recovery timeout."""
        # Open the circuit
        self.circuit_breaker.record_failure()
        self.circuit_breaker.record_failure()
        self.circuit_breaker.record_failure()
        assert self.circuit_breaker.state == "OPEN"
        assert self.circuit_breaker.allow_request() is False

        # Wait for recovery timeout
        time.sleep(1.1)
        assert self.circuit_breaker.allow_request() is True
        assert self.circuit_breaker.state == "HALF-OPEN"

    def test_half_open_state(self):
        """Test half-open state behavior."""
        # Open the circuit
        self.circuit_breaker.record_failure()
        self.circuit_breaker.record_failure()
        self.circuit_breaker.record_failure()
        assert self.circuit_breaker.state == "OPEN"

        # Transition to half-open
        self.circuit_breaker.state = "HALF-OPEN"
        assert self.circuit_breaker.allow_request() is True

        # Record success to close the circuit
        self.circuit_breaker.record_success()
        assert self.circuit_breaker.state == "CLOSED"
        assert self.circuit_breaker.failure_count == 0


class TestRetryDecorator(unittest.TestCase):
    """Test cases for the retry decorator."""

    def test_successful_execution(self):
        """Test successful execution without retries."""
        mock_func = MagicMock(return_value="success")
        decorated_func = retry()(mock_func)
        result = decorated_func("test_endpoint")
        assert result == "success"
        mock_func.assert_called_once_with("test_endpoint")

    def test_retry_on_exception(self):
        """Test retry on exception."""
        mock_func = MagicMock(side_effect=[APIClientError("error"), "success"])
        decorated_func = retry(initial_delay=0.01)(mock_func)
        result = decorated_func("test_endpoint")
        assert result == "success"
        assert mock_func.call_count == 2

    def test_max_retries_exceeded(self):
        """Test max retries exceeded."""
        mock_func = MagicMock(side_effect=APIClientError("error"))
        decorated_func = retry(max_retries=2, initial_delay=0.01)(mock_func)
        with pytest.raises(APIClientError):
            decorated_func("test_endpoint")
        assert mock_func.call_count == 3  # Initial call + 2 retries

    def test_no_retry_on_non_retryable_exception(self):
        """Test no retry on non-retryable exception."""
        mock_func = MagicMock(side_effect=ValueError("error"))
        decorated_func = retry(initial_delay=0.01)(mock_func)
        with pytest.raises(ValueError):
            decorated_func("test_endpoint")
        mock_func.assert_called_once()

    def test_retry_with_backoff(self):
        """Test retry with backoff."""
        mock_func = MagicMock(
            side_effect=[APIClientError("error"), APIClientError("error"), "success"]
        )
        decorated_func = retry(initial_delay=0.01, backoff_factor=2, jitter=False)(
            mock_func
        )

        start_time = time.time()
        result = decorated_func("test_endpoint")
        elapsed_time = time.time() - start_time

        assert result == "success"
        assert mock_func.call_count == 3
        # First retry: 0.01s, Second retry: 0.02s
        assert elapsed_time >= 0.03

    def test_circuit_breaker_integration(self):
        """Test integration with circuit breaker."""
        # Reset circuit breakers
        from football_match_notification_service.retry import _circuit_breakers

        _circuit_breakers.clear()

        # Create a function that fails enough to open the circuit
        mock_func = MagicMock(side_effect=APIClientError("error"))
        decorated_func = retry(circuit_breaker=True, max_retries=1, initial_delay=0.01)(
            mock_func
        )

        # Call until circuit breaker opens (3 failures)
        with pytest.raises(APIClientError):
            decorated_func("test_endpoint")
        with pytest.raises(APIClientError):
            decorated_func("test_endpoint")
        with pytest.raises(APIClientError):
            decorated_func("test_endpoint")

        # Next call should raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            decorated_func("test_endpoint")

        # Function should not have been called again
        assert mock_func.call_count == 6  # 3 calls with 1 retry each

    def test_rate_limit_handling(self):
        """Test special handling for rate limit errors."""
        mock_func = MagicMock(side_effect=[RateLimitError("rate limited"), "success"])
        decorated_func = retry(initial_delay=0.01)(mock_func)
        result = decorated_func("test_endpoint")
        assert result == "success"
        assert mock_func.call_count == 2

    def test_get_circuit_breaker(self):
        """Test getting a circuit breaker for an endpoint."""
        # Reset circuit breakers
        from football_match_notification_service.retry import _circuit_breakers

        _circuit_breakers.clear()

        cb1 = get_circuit_breaker("endpoint1")
        cb2 = get_circuit_breaker("endpoint2")
        cb1_again = get_circuit_breaker("endpoint1")

        assert cb1 is not cb2
        assert cb1 is cb1_again
