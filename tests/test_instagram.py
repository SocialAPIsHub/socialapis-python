"""Tests for the Instagram client.

Same shape as test_facebook.py — respx-mocked HTTP, no live calls in CI.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from socialapis import AsyncInstagram, Instagram, ProfileInfo

SAMPLE_PROFILE = {
    "id": "25025320",
    "username": "instagram",
    "fullName": "Instagram",
    "biography": "Discover what's new on Instagram 🌟",
    "followerCount": 670_000_000,
    "followingCount": 50,
    "postsCount": 7_900,
    "isVerified": True,
    "isPrivate": False,
    "isBusiness": True,
    "profilePictureUrl": "https://scontent.cdninstagram.com/profile.jpg",
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
    assert profile.followers == 670_000_000
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
