"""Verify the migration aliases stay exact references to the real classes.

These aliases are part of the public contract — they exist so devs
migrating from kevinzg/facebook-scraper + arc298/instagram-scraper can
grep-replace one import line and keep running. Renaming them,
redirecting them through a wrapper, or accidentally shadowing them
would break that promise.

The tests assert identity (`is`), not equality — only `is` catches
"someone wrapped the alias in a subclass".
"""

from __future__ import annotations

from socialapis import (
    AsyncFacebook,
    AsyncFacebookScraper,
    AsyncInstagram,
    AsyncInstagramScraper,
    Facebook,
    FacebookScraper,
    Instagram,
    InstagramScraper,
)


def test_facebook_scraper_is_facebook() -> None:
    assert FacebookScraper is Facebook


def test_async_facebook_scraper_is_async_facebook() -> None:
    assert AsyncFacebookScraper is AsyncFacebook


def test_instagram_scraper_is_instagram() -> None:
    assert InstagramScraper is Instagram


def test_async_instagram_scraper_is_async_instagram() -> None:
    assert AsyncInstagramScraper is AsyncInstagram


def test_facebook_scraper_instantiates_like_facebook() -> None:
    fb = FacebookScraper(api_token="t")
    assert isinstance(fb, Facebook)
    fb.close()


def test_instagram_scraper_instantiates_like_instagram() -> None:
    ig = InstagramScraper(api_token="t")
    assert isinstance(ig, Instagram)
    ig.close()
