"""Tests for the Facebook client.

All HTTP calls mocked via `respx`. No live API calls in CI — that would
need a real token (secret leak risk), be flaky (depends on Meta
availability), and waste customer credits.

Coverage focuses on:
    - Identifier normalisation (slug ↔ full URL ↔ numeric ID)
    - The auth header + base URL are correctly applied
    - Each endpoint hits the expected URL with the expected params
    - Error mapping (401 → AuthenticationError, 429 → RateLimitError, etc.)
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

# Mirrors the real API's envelope shape (verified 2026-06-22):
# the page payload sits under string key "0" alongside "message"
# and "meta" envelope keys.
SAMPLE_PAGE_PAYLOAD = {
    "ad_page_id": "206441436112629",
    "user_id": "100064888920170",
    "title": "Engen SA | Cape Town",
    "url": "https://www.facebook.com/EngenSA",
    "category": ["Petroleum Service"],
    "bio": "Energy that drives Africa forward.",
    "description": "Engen SA, Cape Town. 119,213 likes.",
    "address": "Cape Town, South Africa",
    "phone": "+27 860 036 436",
    "email": "1call@engenoil.com",
    "website": "engen.co.za",
    "followers_count": 119000,
    "followers_display": "119K followers",
    "likes_count": 1_234_567,
    "likes_display": "1.2M likes",
    "image": "https://scontent.fbcdn.net/profile.jpg",
    "image_alt": "Engen SA | Cape Town",
    "rating": "66% recommend (327 reviews)",
    "rating_overall": "327",
    "status": "public",
    "is_business_page_active": False,
}
SAMPLE_PAGE_INFO = {
    "0": SAMPLE_PAGE_PAYLOAD,
    "message": "Request completed successfully with status: OK (200)",
    "meta": {"statusCode": 200, "duration": 1143, "creditsCharged": 1},
}


# ============================================================================
# get_page_info — the headline typed-model method
# ============================================================================


@respx.mock
def test_get_page_info_returns_typed_model() -> None:
    respx.get("https://api.socialapis.io/facebook/pages/details").mock(
        return_value=httpx.Response(200, json=SAMPLE_PAGE_INFO)
    )

    with Facebook(api_token="t") as fb:
        page = fb.get_page_info("EngenSA")

    assert isinstance(page, PageInfo)
    assert page.ad_page_id == "206441436112629"
    assert page.title == "Engen SA | Cape Town"
    assert page.likes_count == 1_234_567
    assert page.followers_count == 119000
    assert page.image == "https://scontent.fbcdn.net/profile.jpg"
    assert page.is_business_page_active is False


@respx.mock
def test_get_page_info_accepts_full_url() -> None:
    route = respx.get("https://api.socialapis.io/facebook/pages/details").mock(
        return_value=httpx.Response(200, json=SAMPLE_PAGE_INFO)
    )
    with Facebook(api_token="t") as fb:
        fb.get_page_info("https://www.facebook.com/EngenSA")
    assert route.calls.last.request.url.params["link"] == "https://www.facebook.com/EngenSA"


@respx.mock
def test_get_page_info_normalises_bare_slug() -> None:
    route = respx.get("https://api.socialapis.io/facebook/pages/details").mock(
        return_value=httpx.Response(200, json=SAMPLE_PAGE_INFO)
    )
    with Facebook(api_token="t") as fb:
        fb.get_page_info("EngenSA")
    assert route.calls.last.request.url.params["link"] == "https://www.facebook.com/EngenSA"


@respx.mock
def test_get_page_info_sends_auth_header() -> None:
    route = respx.get("https://api.socialapis.io/facebook/pages/details").mock(
        return_value=httpx.Response(200, json=SAMPLE_PAGE_INFO)
    )
    with Facebook(api_token="my_secret") as fb:
        fb.get_page_info("EngenSA")
    assert route.calls.last.request.headers["x-api-token"] == "my_secret"


def test_missing_api_token_raises_immediately() -> None:
    with pytest.raises(ValueError, match="api_token is required"):
        Facebook(api_token="")


# ============================================================================
# Endpoint coverage — one assertion per category to confirm URL routing
# ============================================================================


@respx.mock
def test_get_page_posts_hits_pages_posts_endpoint() -> None:
    route = respx.get("https://api.socialapis.io/facebook/pages/posts").mock(
        return_value=httpx.Response(200, json={"posts": []})
    )
    with Facebook(api_token="t") as fb:
        fb.get_page_posts("EngenSA")
    assert route.called


@respx.mock
def test_get_group_id_routes_to_groups_id_endpoint() -> None:
    route = respx.get("https://api.socialapis.io/facebook/groups/id").mock(
        return_value=httpx.Response(200, json={"id": "187988788687356"})
    )
    with Facebook(api_token="t") as fb:
        fb.get_group_id("gieldagryplanszowe")
    # Bare slug normalises to /groups/ URL
    assert route.calls.last.request.url.params["link"] == (
        "https://www.facebook.com/groups/gieldagryplanszowe"
    )


@respx.mock
def test_search_pages_passes_query_and_extra_kwargs() -> None:
    route = respx.get("https://api.socialapis.io/facebook/search/pages").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    with Facebook(api_token="t") as fb:
        fb.search_pages("marketing", location_id="103006566409959")
    params = route.calls.last.request.url.params
    assert params["query"] == "marketing"
    assert params["location_id"] == "103006566409959"


@respx.mock
def test_search_ads_routes_to_ads_search() -> None:
    route = respx.get("https://api.socialapis.io/facebook/ads/search").mock(
        return_value=httpx.Response(200, json={"ads": []})
    )
    with Facebook(api_token="t") as fb:
        fb.search_ads("fitness", country="US", activeStatus="Active")
    params = route.calls.last.request.url.params
    assert params["query"] == "fitness"
    assert params["country"] == "US"
    assert params["activeStatus"] == "Active"


@respx.mock
def test_search_marketplace_routes_to_marketplace_search() -> None:
    route = respx.get("https://api.socialapis.io/facebook/marketplace/search").mock(
        return_value=httpx.Response(200, json={"listings": []})
    )
    with Facebook(api_token="t") as fb:
        fb.search_marketplace(
            "cars",
            filter_location_latitude="40.7142",
            filter_location_longitude="-74.0064",
        )
    assert route.called


@respx.mock
def test_get_comment_replies_takes_both_required_params() -> None:
    route = respx.get("https://api.socialapis.io/facebook/posts/comments/replies").mock(
        return_value=httpx.Response(200, json={"replies": []})
    )
    with Facebook(api_token="t") as fb:
        fb.get_comment_replies("FB_COMMENT_ID_X", "EXPANSION_TOKEN_Y")
    params = route.calls.last.request.url.params
    assert params["comment_feedback_id"] == "FB_COMMENT_ID_X"
    assert params["expansion_token"] == "EXPANSION_TOKEN_Y"


@respx.mock
def test_extra_kwargs_forward_to_query_string() -> None:
    """kwargs should land on the request as raw query params — the SDK
    doesn't filter or validate them. This is what makes the SDK
    forward-compatible when the API adds a new filter."""
    route = respx.get("https://api.socialapis.io/facebook/pages/posts").mock(
        return_value=httpx.Response(200, json={"posts": []})
    )
    with Facebook(api_token="t") as fb:
        fb.get_page_posts("EngenSA", end_cursor="abc123", some_future_param="x")
    params = route.calls.last.request.url.params
    assert params["end_cursor"] == "abc123"
    assert params["some_future_param"] == "x"


# ============================================================================
# Error mapping — one per HTTP status the API documents
# ============================================================================


@respx.mock
def test_401_maps_to_authentication_error() -> None:
    respx.get("https://api.socialapis.io/facebook/pages/details").mock(
        return_value=httpx.Response(401, json={"error": "Invalid API token"})
    )
    with Facebook(api_token="bad") as fb, pytest.raises(AuthenticationError) as exc_info:
        fb.get_page_info("EngenSA")
    assert exc_info.value.status_code == 401


@respx.mock
def test_402_maps_to_insufficient_credits_error() -> None:
    respx.get("https://api.socialapis.io/facebook/pages/details").mock(
        return_value=httpx.Response(402, json={"error": "Credit balance exhausted"})
    )
    with Facebook(api_token="t") as fb, pytest.raises(InsufficientCreditsError):
        fb.get_page_info("EngenSA")


@respx.mock
def test_429_maps_to_rate_limit_error_with_retry_after() -> None:
    respx.get("https://api.socialapis.io/facebook/pages/details").mock(
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
    respx.get("https://api.socialapis.io/facebook/pages/details").mock(
        return_value=httpx.Response(400, json={"error": "page not found"})
    )
    with Facebook(api_token="t") as fb, pytest.raises(BadRequestError):
        fb.get_page_info("EngenSA")


# ============================================================================
# Async client smoke test
# ============================================================================


@pytest.mark.asyncio
@respx.mock
async def test_async_get_page_info_works() -> None:
    respx.get("https://api.socialapis.io/facebook/pages/details").mock(
        return_value=httpx.Response(200, json=SAMPLE_PAGE_INFO)
    )
    async with AsyncFacebook(api_token="t") as fb:
        page = await fb.get_page_info("EngenSA")
    assert page.title == "Engen SA | Cape Town"
    assert page.followers_count == 119000


@pytest.mark.asyncio
@respx.mock
async def test_async_search_marketplace_works() -> None:
    respx.get("https://api.socialapis.io/facebook/marketplace/search").mock(
        return_value=httpx.Response(200, json={"listings": []})
    )
    async with AsyncFacebook(api_token="t") as fb:
        result = await fb.search_marketplace("cars")
    assert result == {"listings": []}
