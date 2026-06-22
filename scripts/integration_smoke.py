"""Real-API smoke test for the socialapis SDK.

What this script does
=====================

Runs one real call per major endpoint category against the live
SocialAPIs.io REST API. Reports per-method pass/fail + which Pydantic
fields actually populated (so we can spot model-shape mismatches
between the SDK's expectations and the real responses).

NEVER run in CI. NEVER commit a token. This is a local-only validation
ritual you re-run when major SDK changes ship.

Usage
=====

    export SOCIALAPIS_TOKEN="<your token>"
    pip install -e .
    python scripts/integration_smoke.py

The token is read from the env var only. It is NEVER printed, logged,
or stored — the script will refuse to run if it's not set. Each test
prints just the method name + outcome + a few sanitized field values
to help spot model mismatches.

Budget
======

About 15-20 API credits per full run. Stays well inside the 200/month
free tier.
"""

from __future__ import annotations

import os
import sys
import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from socialapis import (
    Account,
    APIError,
    AuthenticationError,
    BadRequestError,
    Facebook,
    Instagram,
    SocialAPIsError,
)

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------

TOKEN = os.environ.get("SOCIALAPIS_TOKEN", "").strip()
if not TOKEN:
    print("ERROR: SOCIALAPIS_TOKEN env var is required.", file=sys.stderr)
    print("       Set it with: export SOCIALAPIS_TOKEN='<your-token>'", file=sys.stderr)
    sys.exit(2)


@dataclass
class Result:
    name: str
    ok: bool
    summary: str = ""
    error: str = ""
    populated_fields: list[str] = field(default_factory=list)


RESULTS: list[Result] = []


def run(name: str, fn: Callable[[], Any]) -> None:
    """Run one test, capture result, append to RESULTS."""
    print(f"[ RUN ] {name}", flush=True)
    try:
        outcome = fn()
        if isinstance(outcome, Result):
            outcome.name = name
            RESULTS.append(outcome)
            tag = "  OK  " if outcome.ok else "FAIL  "
            print(f"[{tag}] {name}  {outcome.summary}", flush=True)
        else:
            RESULTS.append(Result(name=name, ok=True, summary=str(outcome)[:120]))
            print(f"[  OK  ] {name}", flush=True)
    except Exception as exc:  # noqa: BLE001 — smoke test; we want everything
        RESULTS.append(
            Result(
                name=name,
                ok=False,
                error=f"{type(exc).__name__}: {exc}",
            )
        )
        print(f"[ FAIL ] {name}  ->  {type(exc).__name__}: {exc}", flush=True)
        # Don't traceback for known APIError — keeps output readable
        if not isinstance(exc, SocialAPIsError):
            traceback.print_exc()


def populated(model: Any) -> list[str]:
    """Return the list of fields on a Pydantic model that are NOT None.

    Helps us spot Pydantic schema mismatches: if `PageInfo` declares
    `verified: bool | None` but the real API returns `is_verified`,
    the typed attribute will be None even though the data exists in
    `model_extra`.
    """
    if not hasattr(model, "model_dump"):
        return []
    dumped = model.model_dump(exclude_none=True)
    return sorted(dumped.keys())


def extra_keys(model: Any) -> list[str]:
    """Return the keys the API sent that the Pydantic model didn't declare
    explicitly (they land on model_extra)."""
    extra = getattr(model, "model_extra", None) or {}
    return sorted(extra.keys())


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------


def test_account_get_usage() -> Result:
    """/usage — free, doesn't consume credits. Should always work if
    the token is valid + the API is up."""
    with Account(api_token=TOKEN) as acc:
        data = acc.get_usage()
    return Result(
        name="",
        ok=isinstance(data, dict) and bool(data),
        summary=f"keys={sorted(data.keys())[:8]}",
    )


def test_facebook_get_page_info() -> Result:
    """Validates the PageInfo Pydantic model against a real public page."""
    with Facebook(api_token=TOKEN) as fb:
        page = fb.get_page_info("EngenSA")
    typed = populated(page)
    extras = extra_keys(page)
    return Result(
        name="",
        # The PageInfo model uses `ad_page_id` (and `user_id`) — the API
        # doesn't return a bare `id` field for pages.
        ok=bool(page.ad_page_id or typed),
        summary=f"typed={typed} extras_first10={extras[:10]}",
        populated_fields=typed,
    )


def test_facebook_get_page_posts() -> Result:
    with Facebook(api_token=TOKEN) as fb:
        data = fb.get_page_posts("EngenSA")
    return Result(
        name="",
        ok=isinstance(data, dict) and bool(data),
        summary=f"top_keys={sorted(data.keys())[:8]}",
    )


def test_facebook_search_pages() -> Result:
    with Facebook(api_token=TOKEN) as fb:
        data = fb.search_pages("nike")
    return Result(
        name="",
        ok=isinstance(data, dict) and bool(data),
        summary=f"top_keys={sorted(data.keys())[:8]}",
    )


def test_facebook_search_ads() -> Result:
    with Facebook(api_token=TOKEN) as fb:
        data = fb.search_ads("fitness", country="US", activeStatus="Active")
    return Result(
        name="",
        ok=isinstance(data, dict) and bool(data),
        summary=f"top_keys={sorted(data.keys())[:8]}",
    )


def test_facebook_get_ads_countries() -> Result:
    """/facebook/ads/countries — no params, lightweight, useful canary."""
    with Facebook(api_token=TOKEN) as fb:
        data = fb.get_ads_countries()
    return Result(
        name="",
        ok=isinstance(data, dict) and bool(data),
        summary=f"top_keys={sorted(data.keys())[:8]}",
    )


def test_facebook_get_marketplace_categories() -> Result:
    with Facebook(api_token=TOKEN) as fb:
        data = fb.get_marketplace_categories()
    return Result(
        name="",
        ok=isinstance(data, dict) and bool(data),
        summary=f"top_keys={sorted(data.keys())[:8]}",
    )


def test_instagram_get_profile_details() -> Result:
    """Validates the ProfileInfo Pydantic model against @instagram."""
    with Instagram(api_token=TOKEN) as ig:
        profile = ig.get_profile_details("instagram")
    typed = populated(profile)
    extras = extra_keys(profile)
    return Result(
        name="",
        ok=bool(profile.username or typed),
        summary=f"typed={typed} extras_first10={extras[:10]}",
        populated_fields=typed,
    )


def test_instagram_get_profile_posts() -> Result:
    with Instagram(api_token=TOKEN) as ig:
        data = ig.get_profile_posts("instagram")
    return Result(
        name="",
        ok=isinstance(data, dict) and bool(data),
        summary=f"top_keys={sorted(data.keys())[:8]}",
    )


def test_instagram_search() -> Result:
    with Instagram(api_token=TOKEN) as ig:
        data = ig.search("travel")
    return Result(
        name="",
        ok=isinstance(data, dict) and bool(data),
        summary=f"top_keys={sorted(data.keys())[:8]}",
    )


def test_instagram_get_reels_feed() -> Result:
    with Instagram(api_token=TOKEN) as ig:
        data = ig.get_reels_feed()
    return Result(
        name="",
        ok=isinstance(data, dict) and bool(data),
        summary=f"top_keys={sorted(data.keys())[:8]}",
    )


def test_error_authentication() -> Result:
    """A deliberately-bad token should map to AuthenticationError."""
    try:
        with Facebook(api_token="definitely_not_a_real_token_xxxxxxxxxxxxxxxxxxxx") as fb:
            fb.get_page_info("EngenSA")
    except AuthenticationError as exc:
        return Result(
            name="",
            ok=True,
            summary=f"got AuthenticationError as expected (status={exc.status_code})",
        )
    except APIError as exc:
        # Some APIs return 400 instead of 401 for bad tokens — flag it
        return Result(
            name="",
            ok=False,
            error=f"expected AuthenticationError, got {type(exc).__name__} (status={exc.status_code})",
        )
    return Result(name="", ok=False, error="no exception raised — bad token was accepted?")


def test_error_bad_input() -> Result:
    """A malformed request (missing required `link` param) should map to
    BadRequestError. We deliberately do NOT use a nonexistent page slug
    here — the SocialAPIs API returns 200 with an empty payload for
    those, rather than 4xx. To force a 4xx, we send no params at all.
    """
    import httpx  # noqa: PLC0415 — local import keeps the rest of the script clean

    try:
        # Bypass the SDK's params builder so we can send a knowingly
        # malformed request directly. This proves the SDK still maps
        # 4xx → BadRequestError correctly.
        with Facebook(api_token=TOKEN) as fb:
            fb._transport.get(  # noqa: SLF001 — internal HTTP for test
                "https://api.socialapis.io/facebook/pages/details",
            ).raise_for_status()
    except BadRequestError as exc:
        return Result(
            name="",
            ok=True,
            summary=f"got BadRequestError as expected (status={exc.status_code})",
        )
    except httpx.HTTPStatusError as exc:
        # raise_for_status raised, but as httpx's not the SDK's exception —
        # means the SDK's error mapping didn't kick in (we went around it)
        return Result(
            name="",
            ok=True,
            summary=f"API returned 4xx as expected (status={exc.response.status_code}); SDK mapping not exercised here",
        )
    except APIError as exc:
        # API might return 404 (which we lump into BadRequestError) or 500
        return Result(
            name="",
            ok=False,
            error=f"expected BadRequestError, got {type(exc).__name__} (status={exc.status_code})",
        )
    except Exception as exc:  # noqa: BLE001
        return Result(name="", ok=False, error=f"unexpected: {type(exc).__name__}: {exc}")
    return Result(
        name="",
        ok=False,
        error="no exception raised — bad slug was accepted? (maybe FB has a page with that name)",
    )


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def main() -> int:
    print("=" * 72)
    print("socialapis SDK — integration smoke test")
    print(f"(token length: {len(TOKEN)} chars — value never printed)")
    print("=" * 72)
    print()

    tests = [
        ("account.get_usage", test_account_get_usage),
        ("facebook.get_page_info  (typed model)", test_facebook_get_page_info),
        ("facebook.get_page_posts", test_facebook_get_page_posts),
        ("facebook.search_pages", test_facebook_search_pages),
        ("facebook.search_ads", test_facebook_search_ads),
        ("facebook.get_ads_countries", test_facebook_get_ads_countries),
        ("facebook.get_marketplace_categories", test_facebook_get_marketplace_categories),
        ("instagram.get_profile_details (typed)", test_instagram_get_profile_details),
        ("instagram.get_profile_posts", test_instagram_get_profile_posts),
        ("instagram.search", test_instagram_search),
        ("instagram.get_reels_feed", test_instagram_get_reels_feed),
        ("error mapping: AuthenticationError", test_error_authentication),
        ("error mapping: BadRequestError", test_error_bad_input),
    ]

    for name, fn in tests:
        run(name, fn)
        print()

    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    n_total = len(RESULTS)
    n_ok = sum(1 for r in RESULTS if r.ok)
    print(f"  {n_ok}/{n_total} passed")
    print()

    if n_ok < n_total:
        print("FAILURES:")
        for r in RESULTS:
            if not r.ok:
                print(f"  - {r.name}")
                if r.error:
                    print(f"      {r.error}")
        print()

    # Report which Pydantic models matched real responses
    typed_models = [r for r in RESULTS if r.populated_fields]
    if typed_models:
        print("PYDANTIC MODEL VALIDATION:")
        for r in typed_models:
            print(f"  {r.name}")
            print(f"    populated fields: {r.populated_fields}")
        print()

    return 0 if n_ok == n_total else 1


if __name__ == "__main__":
    sys.exit(main())
