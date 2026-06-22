"""Side-by-side migration example: kevinzg/facebook-scraper → socialapis.

This script demonstrates the one-line import change required to migrate
from the abandoned kevinzg/facebook-scraper library (9.5k stars on
GitHub, broken since ~2022) to the modern hosted `socialapis` SDK.

The shape stays familiar — the `FacebookScraper` alias exists for exactly
this purpose. Method names match kevinzg's where the call shape allows
(`get_page_info`, etc.) and return typed Pydantic models you can autocomplete
in your IDE.

Run this:
    1. Sign up free at https://socialapis.io/auth/signup
    2. export SOCIALAPIS_TOKEN="sk_live_..."
    3. python examples/migrate-from-kevinzg.py
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# BEFORE — kevinzg/facebook-scraper (abandoned, breaks on every Meta change)
# ---------------------------------------------------------------------------
#
# from facebook_scraper import get_page_info, get_posts
#
# page = get_page_info("EngenSA")
# print(page["name"], page["likes"])
#
# for post in get_posts("EngenSA", pages=5):
#     print(post["time"], post["text"][:80])

# ---------------------------------------------------------------------------
# AFTER — socialapis (hosted, typed, maintained)
# ---------------------------------------------------------------------------

from socialapis import FacebookScraper, InsufficientCreditsError, RateLimitError


def main() -> None:
    token = os.environ.get("SOCIALAPIS_TOKEN")
    if not token:
        raise SystemExit(
            "Set SOCIALAPIS_TOKEN — sign up free at "
            "https://socialapis.io/auth/signup"
        )

    # `FacebookScraper` is an alias of `Facebook` — exact same class,
    # different name so migrating imports from kevinzg/facebook-scraper
    # stays a one-liner.
    with FacebookScraper(api_token=token) as fb:
        try:
            page = fb.get_page_info("EngenSA")
        except RateLimitError as exc:
            raise SystemExit(
                f"Rate-limited. Wait {exc.retry_after_seconds}s and retry."
            ) from exc
        except InsufficientCreditsError:
            raise SystemExit(
                "Out of credits. Upgrade at https://socialapis.io/pricing"
            ) from None

    # Same fields kevinzg returned, but now typed (page.name not page["name"])
    print(f"Page: {page.name}")
    print(f"  Category: {page.category}")
    print(f"  Likes:    {page.likes:,}" if page.likes else "  Likes:    n/a")
    print(f"  Verified: {page.verified}")
    print(f"  About:    {page.about}")

    # When v0.2 lands with `get_posts`, this is the equivalent of the
    # kevinzg `for post in get_posts(...):` loop:
    #
    #     for post in fb.iter_posts("EngenSA", limit=50):
    #         print(post.published_at, post.text[:80])


if __name__ == "__main__":
    main()
