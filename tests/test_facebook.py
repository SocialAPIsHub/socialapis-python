"""Tests for the Facebook client.

All HTTP calls are mocked via `respx`. No live API calls in CI — that would
require a real API token (secret leak risk), be flaky (depends on Facebook
availability), and waste customer credits.

Pattern: each test sets up the mocked endpoint, instantiates the client
(sync or async), calls the method, and asserts on the typed model + the
recorded HTTP request shape.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from socialapis import (
    AsyncFacebook,
    AuthenticationError,
    BadRequestError,
    Facebook,
    InsufficientCreditsError,
    PageInfo,
    RateLimitError,
)


# ============================================================================
# Sample upstream responses — mirror the real API's documented shape so
# this also functions as a contract test against the live endpoint.
# ============================================================================

SAMPLE_PAGE_INFO = {
    "id": "143568085655519",
    "name": "Engen SA",
    "url": "https://www.facebook.com/EngenSA",
    "category": "Petroleum Service",
    "likes": 1_234_567,
    "followers": 1_200_000,
    "verified": True,
    "about": "Energy that drives Africa forward.",
    "website": "https://www.engen.com",
    "profileImageUrl": "https://scontent.fbcdn.net/profile.jpg",
    "coverImageUrl": "https://scontent.fbcdn.net/cover.jpg",
}


# ============================================================================
# SYNC TESTS
# ============================================================================

@respx.mock
def test_get_page_info_returns_typed_model() -> None:
    respx.get("https://api.socialapis.io/v1/facebook/page/details").mock(
        return_value=httpx.Response(200, json=SAMPLE_PAGE_INFO)
    )

    with Facebook(api_token="test_token") as fb:
        page = fb.get_page_info("EngenSA")

    assert isinstance(page, PageInfo)
    assert page.id == "143568085655519"
    assert page.name == "Engen SA"
    assert page.likes == 1_234_567
    assert page.verified is True
    # Camel-case API fields populate the snake-case attribute
    assert page.profile_image_url == "https://scontent.fbcdn.net/profile.jpg"


@respx.mock
def test_get_page_info_accepts_full_url() -> None:
    route = respx.get("https://api.socialapis.io/v1/facebook/page/details").mock(
        return_value=httpx.Response(200, json=SAMPLE_PAGE_INFO)
    )

    with Facebook(api_token="test_token") as fb:
        fb.get_page_info("https://www.facebook.com/EngenSA")

    # The SDK should pass the URL through unmodified
    request = route.calls.last.request
    assert request.url.params["link"] == "https://www.facebook.com/EngenSA"


@respx.mock
def test_get_page_info_normalizes_bare_slug() -> None:
    route = respx.get("https://api.socialapis.io/v1/facebook/page/details").mock(
        return_value=httpx.Response(200, json=SAMPLE_PAGE_INFO)
    )

    with Facebook(api_token="test_token") as fb:
        fb.get_page_info("EngenSA")

    # Bare slug should be expanded to the canonical FB URL
    request = route.calls.last.request
    assert request.url.params["link"] == "https://www.facebook.com/EngenSA"


@respx.mock
def test_get_page_info_sends_auth_header() -> None:
    route = respx.get("https://api.socialapis.io/v1/facebook/page/details").mock(
        return_value=httpx.Response(200, json=SAMPLE_PAGE_INFO)
    )

    with Facebook(api_token="my_secret_token") as fb:
        fb.get_page_info("EngenSA")

    assert route.calls.last.request.headers["x-api-token"] == "my_secret_token"


def test_missing_api_token_raises_immediately() -> None:
    with pytest.raises(ValueError, match="api_token is required"):
        Facebook(api_token="")


# ============================================================================
# ERROR-MAPPING TESTS — one per HTTP status the API documents
# ============================================================================

@respx.mock
def test_401_maps_to_authentication_error() -> None:
    respx.get("https://api.socialapis.io/v1/facebook/page/details").mock(
        return_value=httpx.Response(401, json={"error": "Invalid API token"})
    )
    with Facebook(api_token="bad_token") as fb, pytest.raises(AuthenticationError) as exc_info:
        fb.get_page_info("EngenSA")
    assert exc_info.value.status_code == 401
    assert "Invalid API token" in str(exc_info.value)


@respx.mock
def test_402_maps_to_insufficient_credits_error() -> None:
    respx.get("https://api.socialapis.io/v1/facebook/page/details").mock(
        return_value=httpx.Response(402, json={"error": "Credit balance exhausted"})
    )
    with Facebook(api_token="t") as fb, pytest.raises(InsufficientCreditsError) as exc_info:
        fb.get_page_info("EngenSA")
    assert exc_info.value.status_code == 402


@respx.mock
def test_429_maps_to_rate_limit_error_with_retry_after() -> None:
    respx.get("https://api.socialapis.io/v1/facebook/page/details").mock(
        return_value=httpx.Response(
            429,
            json={"error": "Rate limit exceeded"},
            headers={"retry-after": "12"},
        )
    )
    with Facebook(api_token="t") as fb, pytest.raises(RateLimitError) as exc_info:
        fb.get_page_info("EngenSA")
    assert exc_info.value.retry_after_seconds == 12.0


@respx.mock
def test_400_maps_to_bad_request_error() -> None:
    respx.get("https://api.socialapis.io/v1/facebook/page/details").mock(
        return_value=httpx.Response(400, json={"error": "page not found"})
    )
    with Facebook(api_token="t") as fb, pytest.raises(BadRequestError):
        fb.get_page_info("EngenSA")


# ============================================================================
# ASYNC TESTS — same coverage, one method to confirm the async path works
# ============================================================================

@pytest.mark.asyncio
@respx.mock
async def test_async_get_page_info_works() -> None:
    respx.get("https://api.socialapis.io/v1/facebook/page/details").mock(
        return_value=httpx.Response(200, json=SAMPLE_PAGE_INFO)
    )

    async with AsyncFacebook(api_token="t") as fb:
        page = await fb.get_page_info("EngenSA")

    assert page.name == "Engen SA"
    assert page.likes == 1_234_567
