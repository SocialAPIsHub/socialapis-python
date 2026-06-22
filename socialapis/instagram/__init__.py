"""Instagram namespace — Profiles, Posts, Reels, Highlights, Search,
Locations. Mirrors the SocialAPIs.io Instagram REST surface.

Public entry points::

    from socialapis import Instagram, AsyncInstagram

The `InstagramScraper` alias also exists at the package level for users
migrating from the abandoned `arc298/instagram-scraper` library.
"""

from ._client import AsyncInstagram, Instagram
from ._types import ProfileInfo

__all__ = ["AsyncInstagram", "Instagram", "ProfileInfo"]
