"""
Retry mechanism for API requests.

This module provides a retry decorator with exponential backoff and circuit breaker
functionality for handling transient failures in API requests.
"""

import functools
import logging
import random
import time
from typing import Any, Callable, Dict, Optional, Type, Union

import requests

from football_match_notification_service.api_client import (
    APIClientError,
    RateLimitError,
)
from football_match_notification_service.logger import get_logger

# Set up logger
logger = get_logger(__name__)


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""

    pass


class CircuitBreaker:
    """Circuit breaker implementation to prevent repeated calls to failing endpoints."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        """
        Initialize the circuit breaker.

        Args:
            failure_threshold: Number of failures before opening the circuit
            recovery_timeout: Time in seconds before attempting to close the circuit
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN

    def record_success(self) -> None:
        """Record a successful call and reset the circuit breaker."""
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self) -> None:
        """Record a failed call and potentially open the circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )

    def allow_request(self) -> bool:
        """
        Check if a request is allowed based on the circuit state.

        Returns:
            bool: True if the request is allowed, False otherwise
        """
        if self.state == "CLOSED":
            return True

        if self.state == "OPEN":
            # Check if recovery timeout has elapsed
            if time.time() - self.last_failure_time > self.recovery_timeout:
                logger.info("Circuit breaker transitioning to HALF-OPEN state")
                self.state = "HALF-OPEN"
                return True
            return False

        # HALF-OPEN state - allow one request to test if the service is back
        return True


# Global circuit breakers for different endpoints
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(endpoint: str) -> CircuitBreaker:
    """
    Get or create a circuit breaker for an endpoint.

    Args:
        endpoint: API endpoint

    Returns:
        CircuitBreaker: Circuit breaker instance
    """
    if endpoint not in _circuit_breakers:
        _circuit_breakers[endpoint] = CircuitBreaker()
    return _circuit_breakers[endpoint]


def retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[tuple] = None,
    circuit_breaker: bool = True,
):
    """
    Retry decorator with exponential backoff.

    Args:
        max_retries: Maximum number of retries
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Factor to increase delay with each retry
        jitter: Whether to add random jitter to delay
        retry_on_exceptions: Tuple of exceptions to retry on
        circuit_breaker: Whether to use circuit breaker pattern

    Returns:
        Callable: Decorated function
    """
    if retry_on_exceptions is None:
        retry_on_exceptions = (requests.RequestException, APIClientError)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Extract endpoint from args or kwargs for circuit breaker
            endpoint = _extract_endpoint(args, kwargs)

            # Get circuit breaker if enabled
            cb = get_circuit_breaker(endpoint) if circuit_breaker else None

            # Check if circuit breaker is open
            if cb and not cb.allow_request():
                logger.warning(f"Circuit breaker open for endpoint {endpoint}")
                raise CircuitBreakerError(
                    f"Circuit breaker open for endpoint {endpoint}"
                )

            retries = 0
            delay = initial_delay

            while True:
                try:
                    result = func(*args, **kwargs)

                    # Record success if using circuit breaker
                    if cb:
                        cb.record_success()

                    return result

                except RateLimitError as e:
                    # Special handling for rate limiting
                    logger.warning(f"Rate limit exceeded: {str(e)}")

                    # Record failure if using circuit breaker
                    if cb:
                        cb.record_failure()

                    if retries >= max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for rate limit"
                        )
                        raise

                    # Use a longer delay for rate limiting
                    current_delay = min(max_delay, delay * 2)

                except retry_on_exceptions as e:
                    # Don't retry on 4xx errors (except 429 which is handled above)
                    if (
                        isinstance(e, requests.HTTPError)
                        and 400 <= e.response.status_code < 500
                        and e.response.status_code != 429
                    ):
                        logger.error(f"Non-retryable error: {str(e)}")

                        # Record failure if using circuit breaker
                        if cb:
                            cb.record_failure()

                        raise

                    logger.warning(f"Retryable error: {str(e)}")

                    # Record failure if using circuit breaker
                    if cb:
                        cb.record_failure()

                    if retries >= max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded")
                        raise

                    current_delay = min(max_delay, delay)

                except Exception as e:
                    # Record failure if using circuit breaker
                    if cb:
                        cb.record_failure()

                    # Don't retry on non-retryable exceptions
                    logger.error(f"Non-retryable exception: {str(e)}")
                    raise

                # Add jitter to delay if enabled
                if jitter:
                    current_delay = current_delay * (0.5 + random.random())

                logger.info(
                    f"Retrying in {current_delay:.2f} seconds (retry {retries + 1}/{max_retries})"
                )
                time.sleep(current_delay)

                # Increase delay for next retry
                delay = min(max_delay, delay * backoff_factor)
                retries += 1

        return wrapper

    return decorator


def _extract_endpoint(args: tuple, kwargs: dict) -> str:
    """
    Extract endpoint from function arguments.

    Args:
        args: Function positional arguments
        kwargs: Function keyword arguments

    Returns:
        str: Endpoint string or "unknown"
    """
    # Try to extract endpoint from kwargs
    if "endpoint" in kwargs:
        return str(kwargs["endpoint"])

    # If first arg is a string, assume it's the endpoint
    if args and isinstance(args[0], str):
        return args[0]

    return "unknown"
