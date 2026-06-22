"""SocialAPIs Python SDK — Facebook + Instagram public data.

Quick start::

    from socialapis import Facebook, Instagram

    fb = Facebook(api_token="YOUR_API_TOKEN")
    page = fb.get_page_info("EngenSA")

    ig = Instagram(api_token="YOUR_API_TOKEN")
    profile = ig.get_profile_details("instagram")

Async variants::

    from socialapis import AsyncFacebook, AsyncInstagram

    async with AsyncFacebook(api_token="...") as fb:
        page = await fb.get_page_info("EngenSA")

Migration aliases — the import line is the only change from kevinzg /
arc298 abandoned scrapers::

    from socialapis import FacebookScraper           # alias of Facebook
    from socialapis import InstagramScraper          # alias of Instagram

Errors callers commonly handle::

    from socialapis import (
        AuthenticationError,           # 401 — bad token
        InsufficientCreditsError,      # 402 — out of credits
        RateLimitError,                # 429 — slow down
    )

Account info (free, doesn't consume credits)::

    from socialapis import Account

    with Account(api_token="...") as acc:
        usage = acc.get_usage()

Free 200 calls / month: https://socialapis.io/auth/signup
Full docs: https://docs.socialapis.io
"""

from ._account import Account, AsyncAccount
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
from .facebook import AsyncFacebook, Facebook, GroupInfo, PageInfo
from .instagram import AsyncInstagram, Instagram, ProfileInfo

# ---------------------------------------------------------------------------
# Migration aliases — preserve familiar names from abandoned libraries so
# devs can swap their import line and keep running.
#
# `FacebookScraper` mirrors the kevinzg/facebook-scraper entry point
# (9.5k stars on GitHub, abandoned since ~2022).
#
# `InstagramScraper` mirrors arc298/instagram-scraper (8.5k stars,
# sporadic maintenance).
#
# Aliases are EXACT references — identical behavior, identical
# type signatures, just different names. `test_aliases.py` asserts
# this contract so accidental decoupling fails CI.
#
# When a new abandoned library becomes worth capturing, add an alias
# here.
# ---------------------------------------------------------------------------
FacebookScraper = Facebook
AsyncFacebookScraper = AsyncFacebook
InstagramScraper = Instagram
AsyncInstagramScraper = AsyncInstagram


__all__ = [
    # Primary clients
    "Facebook",
    "AsyncFacebook",
    "Instagram",
    "AsyncInstagram",
    "Account",
    "AsyncAccount",
    # Migration aliases (kevinzg + arc298 capture)
    "FacebookScraper",
    "AsyncFacebookScraper",
    "InstagramScraper",
    "AsyncInstagramScraper",
    # Response models
    "PageInfo",
    "GroupInfo",
    "ProfileInfo",
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
