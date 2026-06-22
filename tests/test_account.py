"""Tests for the Account (usage / credits / limits) client."""

from __future__ import annotations

import httpx
import pytest
import respx

from socialapis import Account, AsyncAccount


@respx.mock
def test_get_usage_routes_to_usage_endpoint() -> None:
    respx.get("https://api.socialapis.io/usage").mock(
        return_value=httpx.Response(
            200,
            json={"credits": {"remaining": 198, "limit": 200}, "plan": "free"},
        )
    )
    with Account(api_token="t") as acc:
        usage = acc.get_usage()
    assert usage["credits"]["remaining"] == 198


@respx.mock
def test_get_top_ups_routes_to_top_ups_endpoint() -> None:
    route = respx.get("https://api.socialapis.io/usage/top-ups").mock(
        return_value=httpx.Response(200, json={"enabled": False})
    )
    with Account(api_token="t") as acc:
        acc.get_top_ups()
    assert route.called


@respx.mock
def test_get_limits_routes_to_limits_endpoint() -> None:
    route = respx.get("https://api.socialapis.io/usage/limits").mock(
        return_value=httpx.Response(200, json={"rate_limit": "1000/hour"})
    )
    with Account(api_token="t") as acc:
        acc.get_limits()
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_async_account_works() -> None:
    respx.get("https://api.socialapis.io/usage").mock(
        return_value=httpx.Response(200, json={"credits": {"remaining": 100}})
    )
    async with AsyncAccount(api_token="t") as acc:
        usage = await acc.get_usage()
    assert usage["credits"]["remaining"] == 100
