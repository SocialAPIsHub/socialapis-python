"""Verify the migration aliases stay exact references to the real classes.

These aliases are part of the public contract — they exist so devs
migrating from kevinzg/facebook-scraper can grep-replace one import
line and keep running. Renaming them, redirecting them through a
wrapper, or accidentally shadowing them would break that promise.

Test catches any future change that decouples the alias from the
underlying class.
"""

from __future__ import annotations

from socialapis import (
    AsyncFacebook,
    AsyncFacebookScraper,
    Facebook,
    FacebookScraper,
)


def test_facebook_scraper_is_facebook() -> None:
    """The kevinzg-name alias must be EXACTLY the Facebook class — same
    object identity, not a subclass, not a wrapper."""
    assert FacebookScraper is Facebook


def test_async_facebook_scraper_is_async_facebook() -> None:
    """Same contract on the async side."""
    assert AsyncFacebookScraper is AsyncFacebook


def test_facebook_scraper_instantiates_like_facebook() -> None:
    """End-to-end smoke check — using the alias as a constructor works."""
    fb = FacebookScraper(api_token="test_token")
    assert isinstance(fb, Facebook)
    fb.close()
