"""Quick-start example for the SocialAPIs Python SDK.

Run this:
    1. Sign up free at https://socialapis.io/auth/signup (200 calls/month, no card)
    2. Copy your API token from the dashboard
    3. Set it as an env var:  export SOCIALAPIS_TOKEN="..."
    4. Run:  python examples/quickstart.py
"""

from __future__ import annotations

import os

from socialapis import (
    Account,
    AuthenticationError,
    Facebook,
    InsufficientCreditsError,
    Instagram,
    RateLimitError,
)


def main() -> None:
    token = os.environ.get("SOCIALAPIS_TOKEN")
    if not token:
        raise SystemExit(
            "Set SOCIALAPIS_TOKEN — sign up free at https://socialapis.io/auth/signup"
        )

    # Account info first — confirms the token works + shows your budget
    with Account(api_token=token) as acc:
        try:
            usage = acc.get_usage()
        except AuthenticationError as exc:
            raise SystemExit(f"Bad token: {exc}") from exc
    print("Account:")
    print(f"  Credits:   {usage}")
    print()

    # Facebook
    with Facebook(api_token=token) as fb:
        try:
            page = fb.get_page_info("EngenSA")
        except (RateLimitError, InsufficientCreditsError) as exc:
            raise SystemExit(f"Facebook call failed: {exc}") from exc
    print(f"Facebook page: {page.name}")
    print(f"  Category:  {page.category}")
    print(f"  Likes:     {page.likes:,}" if page.likes else "  Likes:     n/a")
    print(f"  Followers: {page.followers:,}" if page.followers else "  Followers: n/a")
    print(f"  Verified:  {page.verified}")
    print()

    # Instagram
    with Instagram(api_token=token) as ig:
        try:
            profile = ig.get_profile_details("instagram")
        except (RateLimitError, InsufficientCreditsError) as exc:
            raise SystemExit(f"Instagram call failed: {exc}") from exc
    print(f"Instagram profile: @{profile.username}")
    print(f"  Full name: {profile.full_name}")
    print(f"  Followers: {profile.followers:,}" if profile.followers else "  Followers: n/a")
    print(f"  Posts:     {profile.posts_count}")
    print(f"  Verified:  {profile.is_verified}")


if __name__ == "__main__":
    main()
