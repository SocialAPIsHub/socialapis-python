"""Tests for the Instagram client.

Same shape as test_facebook.py — respx-mocked HTTP, no live calls in CI.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from socialapis import AsyncInstagram, Instagram, ProfileInfo

# Mirrors the real API's envelope shape (verified 2026-06-22):
# the profile payload sits under "data" alongside "success",
# "message", and "meta".
SAMPLE_PROFILE_PAYLOAD = {
    "id": "25025320",
    "pk": "25025320",
    "fbid": "17841400039600391",
    "username": "instagram",
    "full_name": "Instagram",
    "biography": "Discover what's new on Instagram",
    "profile_pic_url": "https://scontent.cdninstagram.com/profile.jpg",
    "profile_pic_url_hd": "https://scontent.cdninstagram.com/profile_hd.jpg",
    "external_url": "https://youtu.be/sample",
    "followers_count": 685_000_000,
    "following_count": 229,
    "media_count": 7_900,
    "is_verified": True,
    "is_private": False,
    "is_business_account": False,
    "is_professional_account": True,
    "account_type": 3,
    "has_clips": True,
    "category_name": "",
}
SAMPLE_PROFILE = {
    "success": True,
    "data": SAMPLE_PROFILE_PAYLOAD,
    "message": "Request completed successfully with status: OK (200)",
    "meta": {"statusCode": 200, "creditsCharged": 1},
}


@respx.mock
def test_get_profile_details_returns_typed_model() -> None:
    respx.get("https://api.socialapis.io/instagram/profile/details").mock(
        return_value=httpx.Response(200, json=SAMPLE_PROFILE)
    )

    with Instagram(api_token="t") as ig:
        profile = ig.get_profile_details("instagram")

    assert isinstance(profile, ProfileInfo)
    assert profile.id == "25025320"
    assert profile.username == "instagram"
    assert profile.full_name == "Instagram"
    assert profile.followers_count == 685_000_000
    assert profile.media_count == 7_900
    assert profile.is_verified is True


@respx.mock
def test_get_user_id_normalises_username_to_url() -> None:
    route = respx.get("https://api.socialapis.io/instagram/user/id").mock(
        return_value=httpx.Response(200, json={"id": "25025320"})
    )
    with Instagram(api_token="t") as ig:
        ig.get_user_id("instagram")
    assert route.calls.last.request.url.params["link"] == "https://www.instagram.com/instagram"


@respx.mock
def test_search_hits_instagram_search_endpoint() -> None:
    route = respx.get("https://api.socialapis.io/instagram/search").mock(
        return_value=httpx.Response(200, json={"users": [], "hashtags": []})
    )
    with Instagram(api_token="t") as ig:
        ig.search("travel")
    assert route.calls.last.request.url.params["keyword"] == "travel"


@respx.mock
def test_get_location_posts_passes_tab_kwarg() -> None:
    route = respx.get("https://api.socialapis.io/instagram/location/posts").mock(
        return_value=httpx.Response(200, json={"posts": []})
    )
    with Instagram(api_token="t") as ig:
        ig.get_location_posts("454547536", tab="ranked")
    params = route.calls.last.request.url.params
    assert params["location_id"] == "454547536"
    assert params["tab"] == "ranked"


@pytest.mark.asyncio
@respx.mock
async def test_async_get_profile_details_works() -> None:
    respx.get("https://api.socialapis.io/instagram/profile/details").mock(
        return_value=httpx.Response(200, json=SAMPLE_PROFILE)
    )
    async with AsyncInstagram(api_token="t") as ig:
        profile = await ig.get_profile_details("instagram")
    assert profile.username == "instagram"
