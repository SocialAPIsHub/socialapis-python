"""Typed exception hierarchy for the SocialAPIs SDK.

Why a hierarchy: callers can catch broadly (`SocialAPIsError`) for "anything
the SDK threw" OR narrowly (`RateLimitError`, `AuthenticationError`,
`InsufficientCreditsError`) for retry/UX decisions. Generic exceptions
(httpx.HTTPError, ValueError, etc.) leaking out of public methods would
force callers to handle library internals — bad SDK shape.

The classes mirror the API's documented error semantics:
- 401 → AuthenticationError
- 402 → InsufficientCreditsError (returned when free-tier budget is spent)
- 429 → RateLimitError
- 4xx (other) → BadRequestError
- 5xx → APIServerError

Anything else (network failure, JSON parse failure) → APIConnectionError.
"""

from __future__ import annotations

from typing import Any


class SocialAPIsError(Exception):
    """Base class for every exception raised by this SDK.

    Catch this if you want one handler for any SDK-originating failure.
    """


class APIConnectionError(SocialAPIsError):
    """Network failure, timeout, or non-JSON response from the API.

    Almost always transient. Safe to retry with backoff.
    """


class APIError(SocialAPIsError):
    """An HTTP error response from the API (4xx or 5xx).

    Subclasses below give callers a typed dispatch on the failure class.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        request_id: str | None = None,
        body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.request_id = request_id
        self.body = body or {}


class BadRequestError(APIError):
    """4xx (excluding 401/402/429). Client-side mistake — missing parameter,
    invalid value, wrong endpoint. NOT safe to retry without fixing input."""


class AuthenticationError(APIError):
    """401 — invalid or missing API token. Retrying won't help; the user
    needs to fix their `api_token`."""


class InsufficientCreditsError(APIError):
    """402 — credit balance exhausted. Retrying after a refill / upgrade
    works. Tracked as a distinct exception so paid integrations can
    auto-top-up on this signal."""


class RateLimitError(APIError):
    """429 — request rate exceeded. Retrying after the `Retry-After`
    interval (exposed as `retry_after_seconds`) is safe and idempotent."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 429,
        retry_after_seconds: float | None = None,
        request_id: str | None = None,
        body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            request_id=request_id,
            body=body,
        )
        self.retry_after_seconds = retry_after_seconds


class APIServerError(APIError):
    """5xx — the API failed. Safe to retry with exponential backoff."""
