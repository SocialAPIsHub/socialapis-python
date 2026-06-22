"""Public sync + async Instagram clients.

Coverage mirrors the SocialAPIs.io Instagram REST surface: profiles,
posts, reels, highlights, search, locations.

Same design as the Facebook clients: each method is a thin wrapper that
normalises the primary identifier and forwards extra params via
``**kwargs`` for forward-compat. No ``limit=`` — the API decides page
size.
"""

from __future__ import annotations

from types import TracebackType
from typing import TYPE_CHECKING, Any

import httpx

from .._client import BaseClient
from .._errors import APIConnectionError
from ..facebook._client import _params  # reuse the param-builder
from ._types import ProfileInfo

if TYPE_CHECKING:
    from typing import Self


def _as_instagram_url(value: str) -> str:
    """Normalise an Instagram identifier (username or full URL) to a
    canonical Instagram profile URL."""
    value = value.strip()
    if not value:
        raise ValueError("identifier is required")
    if value.startswith(("http://", "https://")):
        return value
    return f"https://www.instagram.com/{value.lstrip('/').rstrip('/')}"


# ===========================================================================
# SYNC CLIENT
# ===========================================================================
class Instagram(BaseClient):
    """Synchronous Instagram client.

    Drop-in alternative to ``arc298/instagram-scraper``. Use
    ``socialapis.InstagramScraper`` as a name alias for migration ease.

    Quick start::

        from socialapis import Instagram

        with Instagram(api_token="YOUR_API_TOKEN") as ig:
            profile = ig.get_profile_details("instagram")
            posts = ig.get_profile_posts("instagram")
    """

    def __init__(
        self,
        api_token: str,
        *,
        base_url: str = "https://api.socialapis.io",
        timeout: float = 30.0,
        transport: httpx.Client | None = None,
    ) -> None:
        super().__init__(api_token=api_token, base_url=base_url, timeout=timeout)
        self._transport = transport or httpx.Client(
            timeout=self.timeout,
            headers=self._default_headers(),
        )
        self._owns_transport = transport is None

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_transport:
            self._transport.close()

    # =======================================================================
    # PROFILES
    # =======================================================================

    def get_user_id(self, profile: str, **kwargs: Any) -> dict[str, Any]:
        """Return the numeric Instagram user ID for a username or URL.

        Backed by ``GET /instagram/user/id``.
        """
        return self._get(
            "/instagram/user/id",
            _params(("link", _as_instagram_url(profile)), extra=kwargs),
        ).json()

    def get_profile_details(self, username: str, **kwargs: Any) -> ProfileInfo:
        """Return public Instagram profile metadata.

        Backed by ``GET /instagram/profile/details``.
        """
        response = self._get(
            "/instagram/profile/details",
            _params(("username", username), extra=kwargs),
        )
        return ProfileInfo.model_validate(response.json())

    def get_profile_posts(self, username: str, **kwargs: Any) -> dict[str, Any]:
        """Return recent posts from an Instagram profile.

        Backed by ``GET /instagram/profile/posts``.
        """
        return self._get(
            "/instagram/profile/posts",
            _params(("username", username), extra=kwargs),
        ).json()

    def get_profile_reels(self, user_id: str, **kwargs: Any) -> dict[str, Any]:
        """Return Reels for an Instagram profile.

        Backed by ``GET /instagram/profile/reels``. Takes a numeric
        ``user_id`` (use :meth:`get_user_id` to resolve a username first).
        """
        return self._get(
            "/instagram/profile/reels",
            _params(("user_id", user_id), extra=kwargs),
        ).json()

    def get_profile_highlights(self, user_id: str, **kwargs: Any) -> dict[str, Any]:
        """Return all Story Highlights for a profile, with cover images
        and permalinks.

        Backed by ``GET /instagram/profile/highlights``.
        """
        return self._get(
            "/instagram/profile/highlights",
            _params(("user_id", user_id), extra=kwargs),
        ).json()

    def get_highlight_details(self, highlight_id: str, **kwargs: Any) -> dict[str, Any]:
        """Return all stories within a specific Highlight.

        Backed by ``GET /instagram/highlight/details``.
        """
        return self._get(
            "/instagram/highlight/details",
            _params(("highlight_id", highlight_id), extra=kwargs),
        ).json()

    # =======================================================================
    # POSTS
    # =======================================================================

    def get_post_id(self, post: str, **kwargs: Any) -> dict[str, Any]:
        """Extract the shortcode/ID from any Instagram post URL.

        Backed by ``GET /instagram/post/id``.
        """
        return self._get(
            "/instagram/post/id",
            _params(("link", post), extra=kwargs),
        ).json()

    def get_post_details(self, shortcode: str, **kwargs: Any) -> dict[str, Any]:
        """Return full Instagram post details: media, engagement,
        caption, author.

        Backed by ``GET /instagram/post/details``.
        """
        return self._get(
            "/instagram/post/details",
            _params(("shortcode", shortcode), extra=kwargs),
        ).json()

    # =======================================================================
    # REELS
    # =======================================================================

    def get_reels_feed(self, **kwargs: Any) -> dict[str, Any]:
        """Return the trending Reels feed (or chained-author feed when
        ``user_id`` is passed via kwargs).

        Backed by ``GET /instagram/reels/feed``.
        """
        return self._get(
            "/instagram/reels/feed",
            _params(extra=kwargs),
        ).json()

    def get_reels_by_audio(self, audio_id: str, **kwargs: Any) -> dict[str, Any]:
        """Return all Reels using a specific audio/music track.

        Backed by ``GET /instagram/reels/audio``.
        """
        return self._get(
            "/instagram/reels/audio",
            _params(("audio_id", audio_id), extra=kwargs),
        ).json()

    # =======================================================================
    # SEARCH + LOCATIONS
    # =======================================================================

    def search(self, keyword: str, **kwargs: Any) -> dict[str, Any]:
        """Search Instagram and return popular results — users, hashtags,
        places.

        Backed by ``GET /instagram/search``.
        """
        return self._get(
            "/instagram/search",
            _params(("keyword", keyword), extra=kwargs),
        ).json()

    def get_location_posts(self, location_id: str, **kwargs: Any) -> dict[str, Any]:
        """Return posts tagged at a specific Instagram location.

        Backed by ``GET /instagram/location/posts``. Pass ``tab="ranked"``
        for top posts or ``tab="recent"`` for most-recent.
        """
        return self._get(
            "/instagram/location/posts",
            _params(("location_id", location_id), extra=kwargs),
        ).json()

    def get_nearby_locations(self, location_id: str, **kwargs: Any) -> dict[str, Any]:
        """Return Instagram locations near a given location.

        Backed by ``GET /instagram/location/nearby``.
        """
        return self._get(
            "/instagram/location/nearby",
            _params(("location_id", location_id), extra=kwargs),
        ).json()

    # =======================================================================
    # INTERNAL
    # =======================================================================

    def _get(self, path: str, params: dict[str, str]) -> httpx.Response:
        url = self._build_url(path)
        try:
            response = self._transport.get(url, params=params)
        except httpx.RequestError as exc:
            raise APIConnectionError(f"Request failed: {exc}") from exc
        self._raise_for_status(response)
        return response


# ===========================================================================
# ASYNC CLIENT
# ===========================================================================
class AsyncInstagram(BaseClient):
    """Asynchronous Instagram client. Same surface as :class:`Instagram`;
    every public method is a coroutine.
    """

    def __init__(
        self,
        api_token: str,
        *,
        base_url: str = "https://api.socialapis.io",
        timeout: float = 30.0,
        transport: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(api_token=api_token, base_url=base_url, timeout=timeout)
        self._transport = transport or httpx.AsyncClient(
            timeout=self.timeout,
            headers=self._default_headers(),
        )
        self._owns_transport = transport is None

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_transport:
            await self._transport.aclose()

    # ---- profiles ----------------------------------------------------------

    async def get_user_id(self, profile: str, **kwargs: Any) -> dict[str, Any]:
        return (await self._get(
            "/instagram/user/id",
            _params(("link", _as_instagram_url(profile)), extra=kwargs),
        )).json()

    async def get_profile_details(self, username: str, **kwargs: Any) -> ProfileInfo:
        response = await self._get(
            "/instagram/profile/details",
            _params(("username", username), extra=kwargs),
        )
        return ProfileInfo.model_validate(response.json())

    async def get_profile_posts(self, username: str, **kwargs: Any) -> dict[str, Any]:
        return (await self._get(
            "/instagram/profile/posts",
            _params(("username", username), extra=kwargs),
        )).json()

    async def get_profile_reels(self, user_id: str, **kwargs: Any) -> dict[str, Any]:
        return (await self._get(
            "/instagram/profile/reels",
            _params(("user_id", user_id), extra=kwargs),
        )).json()

    async def get_profile_highlights(self, user_id: str, **kwargs: Any) -> dict[str, Any]:
        return (await self._get(
            "/instagram/profile/highlights",
            _params(("user_id", user_id), extra=kwargs),
        )).json()

    async def get_highlight_details(self, highlight_id: str, **kwargs: Any) -> dict[str, Any]:
        return (await self._get(
            "/instagram/highlight/details",
            _params(("highlight_id", highlight_id), extra=kwargs),
        )).json()

    # ---- posts -------------------------------------------------------------

    async def get_post_id(self, post: str, **kwargs: Any) -> dict[str, Any]:
        return (await self._get(
            "/instagram/post/id",
            _params(("link", post), extra=kwargs),
        )).json()

    async def get_post_details(self, shortcode: str, **kwargs: Any) -> dict[str, Any]:
        return (await self._get(
            "/instagram/post/details",
            _params(("shortcode", shortcode), extra=kwargs),
        )).json()

    # ---- reels -------------------------------------------------------------

    async def get_reels_feed(self, **kwargs: Any) -> dict[str, Any]:
        return (await self._get(
            "/instagram/reels/feed",
            _params(extra=kwargs),
        )).json()

    async def get_reels_by_audio(self, audio_id: str, **kwargs: Any) -> dict[str, Any]:
        return (await self._get(
            "/instagram/reels/audio",
            _params(("audio_id", audio_id), extra=kwargs),
        )).json()

    # ---- search + locations ------------------------------------------------

    async def search(self, keyword: str, **kwargs: Any) -> dict[str, Any]:
        return (await self._get(
            "/instagram/search",
            _params(("keyword", keyword), extra=kwargs),
        )).json()

    async def get_location_posts(self, location_id: str, **kwargs: Any) -> dict[str, Any]:
        return (await self._get(
            "/instagram/location/posts",
            _params(("location_id", location_id), extra=kwargs),
        )).json()

    async def get_nearby_locations(self, location_id: str, **kwargs: Any) -> dict[str, Any]:
        return (await self._get(
            "/instagram/location/nearby",
            _params(("location_id", location_id), extra=kwargs),
        )).json()

    # ---- internal ----------------------------------------------------------

    async def _get(self, path: str, params: dict[str, str]) -> httpx.Response:
        url = self._build_url(path)
        try:
            response = await self._transport.get(url, params=params)
        except httpx.RequestError as exc:
            raise APIConnectionError(f"Request failed: {exc}") from exc
        self._raise_for_status(response)
        return response
