"""Side-by-side migration example: kevinzg/facebook-scraper → socialapis.

This script demonstrates the one-line import change required to migrate
from the abandoned kevinzg/facebook-scraper library (9.5k stars,
broken since ~2022) to the modern hosted `socialapis` SDK.

The shape stays familiar — the `FacebookScraper` alias exists for
exactly this purpose. Method names match kevinzg's where call shape
allows (`get_page_info`, `get_page_posts`, etc.) and return typed
Pydantic models you can autocomplete in your IDE.

Run this:
    1. Sign up free at https://socialapis.io/auth/signup
    2. export SOCIALAPIS_TOKEN="<paste your token from the dashboard>"
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

        # Same data kevinzg returned, but now typed (page.title not page["name"]).
        # Field names match the API exactly — see PageInfo in the SDK docs.
        print(f"Page: {page.title}")
        print(f"  Category: {page.category}")
        print(f"  Likes:    {page.likes_count:,}" if page.likes_count else "  Likes:    n/a")
        print(f"  Followers:{page.followers_count:,}" if page.followers_count else "")

        # kevinzg's `for post in get_posts(...)` equivalent — paginate via cursors
        result = fb.get_page_posts("EngenSA")
        for post in result.get("posts", [])[:5]:
            timestamp = post.get("time") or post.get("published_at", "?")
            text = post.get("text") or post.get("message", "")
            print(f"  [{timestamp}] {text[:80]}")


if __name__ == "__main__":
    main()
