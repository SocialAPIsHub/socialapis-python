"""Internal HTTP client used by both sync and async public APIs.

Why a single internal client: HTTP error mapping, default headers, retry
policy, and timeout config should live in ONE place — not duplicated
between `Facebook` (sync) and `AsyncFacebook` (async). Both call into this
module's helpers.

Architecture:
    BaseClient   — config + URL building + error mapping (no I/O)
    SyncTransport (httpx.Client)
    AsyncTransport (httpx.AsyncClient)

Public callers never import from here; they import `Facebook` / `AsyncFacebook`
from the top-level `socialapis` namespace.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx

from ._errors import (
    APIConnectionError,
    APIServerError,
    AuthenticationError,
    BadRequestError,
    InsufficientCreditsError,
    RateLimitError,
)
from ._version import __version__

if TYPE_CHECKING:
    from collections.abc import Mapping


DEFAULT_BASE_URL = "https://api.socialapis.io"
DEFAULT_TIMEOUT = 30.0
USER_AGENT = f"socialapis-python/{__version__}"


class BaseClient:
    """Shared config + helpers between sync and async public clients.

    Holds the API token, base URL, and default timeout. Knows how to build
    request URLs and translate httpx Responses into typed exceptions.

    NOT meant to be instantiated by end users — `Facebook(api_token=...)`
    and `AsyncFacebook(api_token=...)` wrap this internally.
    """

    def __init__(
        self,
        api_token: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        if not api_token:
            raise ValueError(
                "api_token is required. Get a free key at "
                "https://socialapis.io/auth/signup (200 calls/month, no card)."
            )
        self.api_token = api_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # ---- request preparation ------------------------------------------------

    def _build_url(self, path: str) -> str:
        """Concatenate base URL + path. Path must start with '/'."""
        if not path.startswith("/"):
            raise ValueError(f"path must start with '/', got: {path!r}")
        return f"{self.base_url}{path}"

    def _default_headers(self) -> dict[str, str]:
        return {
            "x-api-token": self.api_token,
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }

    # ---- response → exception mapping ---------------------------------------

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Translate an HTTP error response into a typed SDK exception.

        2xx responses are no-ops. Anything else raises a subclass of
        APIError that callers can catch specifically (RateLimitError,
        InsufficientCreditsError, AuthenticationError, etc.).
        """
        if response.is_success:
            return

        body = _safe_json(response)
        message = _extract_message(body) or response.text or response.reason_phrase
        request_id = response.headers.get("x-request-id")

        status = response.status_code

        if status == 401:
            raise AuthenticationError(
                message,
                status_code=status,
                request_id=request_id,
                body=body,
            )
        if status == 402:
            raise InsufficientCreditsError(
                message,
                status_code=status,
                request_id=request_id,
                body=body,
            )
        if status == 429:
            retry_after = response.headers.get("retry-after")
            raise RateLimitError(
                message,
                status_code=status,
                retry_after_seconds=float(retry_after) if retry_after else None,
                request_id=request_id,
                body=body,
            )
        if 400 <= status < 500:
            raise BadRequestError(
                message,
                status_code=status,
                request_id=request_id,
                body=body,
            )
        if 500 <= status < 600:
            raise APIServerError(
                message,
                status_code=status,
                request_id=request_id,
                body=body,
            )

        # Defensive — unreachable for valid HTTP responses
        raise APIConnectionError(f"Unexpected status code {status}: {message}")


def _safe_json(response: httpx.Response) -> dict[str, Any]:
    """Parse the response body as JSON without raising. Non-JSON bodies
    return an empty dict — let the caller decide what to do."""
    try:
        data = response.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _extract_message(body: Mapping[str, Any]) -> str | None:
    """Pull a human-readable error message from the API's error envelope.

    The API uses one of several conventions across endpoints — try the
    common ones in order.
    """
    for key in ("error", "message", "detail"):
        value = body.get(key)
        if isinstance(value, str) and value:
            return value
        if isinstance(value, dict):
            nested = value.get("message")
            if isinstance(nested, str) and nested:
                return nested
    return None
