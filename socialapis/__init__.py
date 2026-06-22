"""SocialAPIs Python SDK — Facebook + Instagram public data.

The fast way to integrate:

    from socialapis import Facebook

    fb = Facebook(api_token="sk_live_...")
    page = fb.get_page_info("EngenSA")
    print(page.name, page.likes, page.category)

Async variant:

    from socialapis import AsyncFacebook

    async with AsyncFacebook(api_token="sk_live_...") as fb:
        page = await fb.get_page_info("EngenSA")

Migrating from kevinzg/facebook-scraper? The `FacebookScraper` alias keeps
your imports greppable while you do the change:

    from socialapis import FacebookScraper

    fb = FacebookScraper(api_token="...")
    page = fb.get_page_info("EngenSA")    # same method names as kevinzg

Errors that callers commonly catch:

    from socialapis import (
        AuthenticationError,           # 401 — bad token
        InsufficientCreditsError,      # 402 — out of credits
        RateLimitError,                # 429 — slow down
    )

Full docs: https://docs.socialapis.io
Free 200 calls / month: https://socialapis.io/auth/signup
"""

from ._errors import (
    APIConnectionError,
    APIError,
    APIServerError,
    AuthenticationError,
    BadRequestError,
    InsufficientCreditsError,
    RateLimitError,
    SocialAPIsError,
)
from ._version import __version__
from .facebook import AsyncFacebook, Facebook, PageInfo

# ---------------------------------------------------------------------------
# Migration aliases — preserve familiar names from abandoned libraries so
# devs can swap their import line and keep running.
#
# `FacebookScraper` (and `AsyncFacebookScraper`) mirror the conceptual
# entry point of kevinzg/facebook-scraper (the 9.5k-star library that's
# been abandoned since 2022). Aliases are exact references to `Facebook`
# / `AsyncFacebook` — identical behavior, identical type signatures —
# they exist purely so `from socialapis import FacebookScraper` works
# unchanged for migrating users.
#
# When a new "abandoned library" comes online and we want to capture
# its audience too, add an alias here (e.g. `InstagramScraper` for
# arc298/instagram-scraper migrants once the Instagram namespace lands).
# ---------------------------------------------------------------------------
FacebookScraper = Facebook
AsyncFacebookScraper = AsyncFacebook


__all__ = [
    # Clients
    "Facebook",
    "AsyncFacebook",
    # Migration aliases
    "FacebookScraper",
    "AsyncFacebookScraper",
    # Models
    "PageInfo",
    # Exceptions
    "SocialAPIsError",
    "APIError",
    "APIConnectionError",
    "APIServerError",
    "AuthenticationError",
    "BadRequestError",
    "InsufficientCreditsError",
    "RateLimitError",
    # Metadata
    "__version__",
]
