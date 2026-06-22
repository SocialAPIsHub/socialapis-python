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
    AuthenticationError,
    Facebook,
    InsufficientCreditsError,
    RateLimitError,
)


def main() -> None:
    token = os.environ.get("SOCIALAPIS_TOKEN")
    if not token:
        raise SystemExit(
            "Set SOCIALAPIS_TOKEN — sign up free at https://socialapis.io/auth/signup"
        )

    with Facebook(api_token=token) as fb:
        try:
            page = fb.get_page_info("EngenSA")
        except AuthenticationError as exc:
            raise SystemExit(f"Bad token: {exc}") from exc
        except InsufficientCreditsError:
            raise SystemExit(
                "Out of credits. Upgrade at https://socialapis.io/pricing"
            ) from None
        except RateLimitError as exc:
            raise SystemExit(
                f"Rate-limited. Wait {exc.retry_after_seconds}s and retry."
            ) from exc

    print(f"Page: {page.name}")
    print(f"  Category:  {page.category}")
    print(f"  Likes:     {page.likes:,}" if page.likes else "  Likes:     n/a")
    print(f"  Followers: {page.followers:,}" if page.followers else "  Followers: n/a")
    print(f"  Verified:  {page.verified}")
    print(f"  URL:       {page.url}")


if __name__ == "__main__":
    main()
