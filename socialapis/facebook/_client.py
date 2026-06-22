"""Public sync + async Facebook clients.

Method coverage mirrors the SocialAPIs.io REST surface for Facebook (Pages,
Groups, Posts, Search, Ads Library, Marketplace, Media). Each method is a
thin wrapper:

    1. Normalise the primary identifier (a Facebook URL/slug → a `link`
       query param; a bare ID → the appropriate `_id` query param).
    2. Forward any additional query params via `**kwargs` so the SDK
       stays forward-compatible when the API adds a new filter — no
       client release needed to pick up new behavior.
    3. Issue the HTTP call (sync via `httpx.Client`, async via
       `httpx.AsyncClient`).
    4. Return the parsed JSON. The five "headline" methods return typed
       Pydantic models (PageInfo, GroupInfo) for IDE autocomplete on the
       most-used responses; the rest return plain `dict[str, Any]` —
       callers who want type safety can validate themselves.

Pagination: when the API returns a cursor, it appears in the response
body under whichever key the endpoint documents (varies by route —
`end_cursor`, `cursor_token`, `next`, etc.). Pass that cursor back in
via `**kwargs` on the next call. We do NOT impose a `limit=` parameter
— the API decides page size, callers iterate cursors. This matches the
underlying REST semantics and avoids drift between SDK and API.
"""

from __future__ import annotations

from types import TracebackType
from typing import TYPE_CHECKING, Any

import httpx

from .._client import BaseClient
from .._errors import APIConnectionError
from ._types import GroupInfo, PageInfo

if TYPE_CHECKING:
    # `Self` is in typing as of Python 3.11; for our 3.10 baseline we
    # use the typing_extensions backport. typing_extensions is already
    # a transitive dependency of pydantic, so no extra install.
    from typing_extensions import Self


# ---------------------------------------------------------------------------
# Identifier normalisation
#
# Several endpoints accept either a full Facebook URL OR a bare slug/ID,
# but the API itself only takes one shape per endpoint. These helpers let
# users pass whichever form is natural and we coerce to what the API
# expects.
# ---------------------------------------------------------------------------


def _as_facebook_url(value: str, base: str = "https://www.facebook.com") -> str:
    """Normalise a slug or full URL to a canonical Facebook URL.

    Examples::

        "EngenSA"                              → "https://www.facebook.com/EngenSA"
        "https://www.facebook.com/EngenSA"     → unchanged
        "https://m.facebook.com/EngenSA"       → unchanged
    """
    value = value.strip()
    if not value:
        raise ValueError("identifier is required")
    if value.startswith(("http://", "https://")):
        return value
    return f"{base}/{value.lstrip('/')}"


def _as_facebook_group_url(value: str) -> str:
    """Normalise a Group identifier (slug, numeric ID, or full URL) to a
    canonical Facebook group URL."""
    value = value.strip()
    if not value:
        raise ValueError("group identifier is required")
    if value.startswith(("http://", "https://")):
        return value
    return f"https://www.facebook.com/groups/{value.lstrip('/')}"


def _params(*pairs: tuple[str, Any], extra: dict[str, Any] | None = None) -> dict[str, str]:
    """Build a query-string-safe dict, dropping None values + stringifying.

    Lets methods declare their primary params as `("link", url)` etc. and
    splat `extra` for any **kwargs. Keeps each method's body to ~5 lines.
    """
    result: dict[str, str] = {}
    for key, value in pairs:
        if value is None:
            continue
        result[key] = str(value)
    if extra:
        for key, value in extra.items():
            if value is None:
                continue
            result[key] = str(value)
    return result


# ===========================================================================
# SYNC CLIENT
# ===========================================================================
class Facebook(BaseClient):
    """Synchronous Facebook client.

    Drop-in alternative to the abandoned kevinzg/facebook-scraper library.
    Use ``socialapis.FacebookScraper`` as a name alias for migration ease.

    All public-data calls route through socialapis.io — no OAuth, no
    Facebook app review, no scraper maintenance. Get a free API token
    (200 calls/month) at https://socialapis.io/auth/signup.

    Quick start::

        from socialapis import Facebook

        with Facebook(api_token="YOUR_API_TOKEN") as fb:
            page = fb.get_page_info("EngenSA")
            posts = fb.get_page_posts("EngenSA")
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

    # ---- context-manager interface -----------------------------------------

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
        """Close the underlying connection pool. Safe to call repeatedly."""
        if self._owns_transport:
            self._transport.close()

    # =======================================================================
    # PAGES
    # =======================================================================

    def get_page_id(self, page: str, **kwargs: Any) -> dict[str, Any]:
        """Return the numeric Facebook Page ID for a given page URL or slug.

        Backed by ``GET /facebook/pages/id``.
        """
        return self._get(
            "/facebook/pages/id",
            _params(("link", _as_facebook_url(page)), extra=kwargs),
        ).json()

    def get_page_info(self, page: str, **kwargs: Any) -> PageInfo:
        """Return public metadata for a Facebook Page.

        Backed by ``GET /facebook/pages/details``. Returns a typed
        :class:`PageInfo` — additional fields the API may return are
        preserved in ``model_extra``.
        """
        response = self._get(
            "/facebook/pages/details",
            _params(("link", _as_facebook_url(page)), extra=kwargs),
        )
        return PageInfo.model_validate(response.json())

    def get_page_posts(self, page: str, **kwargs: Any) -> dict[str, Any]:
        """Return recent posts from a Facebook Page.

        Backed by ``GET /facebook/pages/posts``. The API decides page size.
        For subsequent pages, pass the cursor from the previous response
        (key varies — see the docs for the specific endpoint).
        """
        return self._get(
            "/facebook/pages/posts",
            _params(("link", _as_facebook_url(page)), extra=kwargs),
        ).json()

    def get_page_reels(self, page: str, **kwargs: Any) -> dict[str, Any]:
        """Return Reels (short videos) from a Facebook Page.

        Backed by ``GET /facebook/pages/reels``.
        """
        return self._get(
            "/facebook/pages/reels",
            _params(("link", _as_facebook_url(page)), extra=kwargs),
        ).json()

    def get_page_videos(self, page: str, **kwargs: Any) -> dict[str, Any]:
        """Return long-form videos from a Facebook Page.

        Backed by ``GET /facebook/pages/videos``.
        """
        return self._get(
            "/facebook/pages/videos",
            _params(("link", _as_facebook_url(page)), extra=kwargs),
        ).json()

    # =======================================================================
    # GROUPS
    # =======================================================================

    def get_group_id(self, group: str, **kwargs: Any) -> dict[str, Any]:
        """Return the numeric Facebook Group ID.

        Backed by ``GET /facebook/groups/id``.
        """
        return self._get(
            "/facebook/groups/id",
            _params(("link", _as_facebook_group_url(group)), extra=kwargs),
        ).json()

    def get_group_details(self, group: str, **kwargs: Any) -> GroupInfo:
        """Return rich metadata for a Facebook Group (rules, members, activity).

        Backed by ``GET /facebook/groups/details``.
        """
        response = self._get(
            "/facebook/groups/details",
            _params(("link", _as_facebook_group_url(group)), extra=kwargs),
        )
        return GroupInfo.model_validate(response.json())

    def get_group_metadata(self, group: str, **kwargs: Any) -> dict[str, Any]:
        """Return lightweight Group metadata (name, id, url, image).

        Cheaper than ``get_group_details`` when you only need IDs/names.
        Backed by ``GET /facebook/groups/metadata``.
        """
        return self._get(
            "/facebook/groups/metadata",
            _params(("link", _as_facebook_group_url(group)), extra=kwargs),
        ).json()

    def get_group_posts(self, group: str, **kwargs: Any) -> dict[str, Any]:
        """Return recent posts from a Facebook Group.

        Backed by ``GET /facebook/groups/posts``.
        """
        return self._get(
            "/facebook/groups/posts",
            _params(("link", _as_facebook_group_url(group)), extra=kwargs),
        ).json()

    def get_group_videos(self, group_id: str, **kwargs: Any) -> dict[str, Any]:
        """Return videos posted to a Facebook Group.

        Backed by ``GET /facebook/groups/videos``. Takes a numeric
        ``group_id`` (use :meth:`get_group_id` to resolve a URL first).
        """
        return self._get(
            "/facebook/groups/videos",
            _params(("group_id", group_id), extra=kwargs),
        ).json()

    # =======================================================================
    # POSTS
    # =======================================================================

    def get_post_id(self, post: str, **kwargs: Any) -> dict[str, Any]:
        """Extract the numeric Facebook post ID from a post URL.

        Backed by ``GET /facebook/posts/id``.
        """
        return self._get(
            "/facebook/posts/id",
            _params(("link", post), extra=kwargs),
        ).json()

    def get_post_details(self, post: str, **kwargs: Any) -> dict[str, Any]:
        """Return full details of a Facebook post (reactions, media, author).

        Backed by ``GET /facebook/posts/details``.
        """
        return self._get(
            "/facebook/posts/details",
            _params(("link", post), extra=kwargs),
        ).json()

    def get_post_details_extended(self, post: str, **kwargs: Any) -> dict[str, Any]:
        """Return extended post details (views, video URLs, music info,
        author verification).

        Backed by ``GET /facebook/posts/details/extended``.
        """
        return self._get(
            "/facebook/posts/details/extended",
            _params(("link", post), extra=kwargs),
        ).json()

    def get_post_comments(self, post: str, **kwargs: Any) -> dict[str, Any]:
        """Return comments on a Facebook post or reel.

        Backed by ``GET /facebook/posts/comments``. Pass
        ``include_reply_info="true"`` to get the cursor needed for
        :meth:`get_comment_replies`.
        """
        return self._get(
            "/facebook/posts/comments",
            _params(("link", post), extra=kwargs),
        ).json()

    def get_comment_replies(
        self,
        comment_feedback_id: str,
        expansion_token: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Return replies to a specific comment.

        Backed by ``GET /facebook/posts/comments/replies``. Both inputs
        come from :meth:`get_post_comments` when called with
        ``include_reply_info=true``.
        """
        return self._get(
            "/facebook/posts/comments/replies",
            _params(
                ("comment_feedback_id", comment_feedback_id),
                ("expansion_token", expansion_token),
                extra=kwargs,
            ),
        ).json()

    def get_post_attachments(self, post_id: str, **kwargs: Any) -> dict[str, Any]:
        """Return all media attachments (photos, videos) from a post.

        Backed by ``GET /facebook/posts/attachments``.
        """
        return self._get(
            "/facebook/posts/attachments",
            _params(("post_id", post_id), extra=kwargs),
        ).json()

    def get_video_post_details(self, video_id: str, **kwargs: Any) -> dict[str, Any]:
        """Return title, reactions, and play counts for a video post.

        Backed by ``GET /facebook/posts/video``.
        """
        return self._get(
            "/facebook/posts/video",
            _params(("video_id", video_id), extra=kwargs),
        ).json()

    # =======================================================================
    # SEARCH
    # =======================================================================

    def search_pages(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Search Facebook pages by keyword. Optional location filtering
        via ``location_id`` (use :meth:`search_locations` to resolve a
        place to an ID).

        Backed by ``GET /facebook/search/pages``.
        """
        return self._get(
            "/facebook/search/pages",
            _params(("query", query), extra=kwargs),
        ).json()

    def search_people(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Search Facebook profiles by keyword.

        Backed by ``GET /facebook/search/people``.
        """
        return self._get(
            "/facebook/search/people",
            _params(("query", query), extra=kwargs),
        ).json()

    def search_locations(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Search Facebook for locations matching a keyword. Returns
        location UIDs used by other geo-filtered search endpoints.

        Backed by ``GET /facebook/search/locations``.
        """
        return self._get(
            "/facebook/search/locations",
            _params(("query", query), extra=kwargs),
        ).json()

    def search_posts(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Search Facebook posts by keyword, with optional location and
        time filters.

        Backed by ``GET /facebook/search/posts``.
        """
        return self._get(
            "/facebook/search/posts",
            _params(("query", query), extra=kwargs),
        ).json()

    def search_videos(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Search Facebook videos by keyword, with optional recency / live
        filters.

        Backed by ``GET /facebook/search/videos``.
        """
        return self._get(
            "/facebook/search/videos",
            _params(("query", query), extra=kwargs),
        ).json()

    # =======================================================================
    # ADS LIBRARY (Meta Ads transparency)
    # =======================================================================

    def get_ads_countries(self, **kwargs: Any) -> dict[str, Any]:
        """Return all country codes supported by the Meta Ads Library.

        Backed by ``GET /facebook/ads/countries``.
        """
        return self._get("/facebook/ads/countries", _params(extra=kwargs)).json()

    def search_ads(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Search ads in the Meta Ad Library by keyword.

        Backed by ``GET /facebook/ads/search``. Common filters:
        ``country``, ``activeStatus`` (Active / All / Inactive).
        """
        return self._get(
            "/facebook/ads/search",
            _params(("query", query), extra=kwargs),
        ).json()

    def get_ads_page_details(self, page_id: str, **kwargs: Any) -> dict[str, Any]:
        """Return Ads-Library metadata for a Facebook Page.

        Backed by ``GET /facebook/ads/page-details``.
        """
        return self._get(
            "/facebook/ads/page-details",
            _params(("page_id", page_id), extra=kwargs),
        ).json()

    def get_ad_archive_details(
        self,
        ad_archive_id: str,
        page_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Return detailed info for a specific archived ad: creative,
        spend, impressions.

        Backed by ``GET /facebook/ads/archive-details``.
        """
        return self._get(
            "/facebook/ads/archive-details",
            _params(
                ("ad_archive_id", ad_archive_id),
                ("page_id", page_id),
                extra=kwargs,
            ),
        ).json()

    def search_ads_by_keywords(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Search ads in the Ad Library by keyword with country filter.

        Backed by ``GET /facebook/ads/keywords``.
        """
        return self._get(
            "/facebook/ads/keywords",
            _params(("query", query), extra=kwargs),
        ).json()

    # =======================================================================
    # MARKETPLACE
    # =======================================================================

    def search_marketplace(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Search Facebook Marketplace listings.

        Backed by ``GET /facebook/marketplace/search``. Common filters:
        ``filter_location_latitude``, ``filter_location_longitude``,
        ``filter_price_max``, ``proxy_country``, ``sort_by``.
        """
        return self._get(
            "/facebook/marketplace/search",
            _params(("query", query), extra=kwargs),
        ).json()

    def get_listing_details(self, listing_id: str, **kwargs: Any) -> dict[str, Any]:
        """Return full info for a Marketplace listing: photos, price,
        seller, delivery.

        Backed by ``GET /facebook/marketplace/listing``.
        """
        return self._get(
            "/facebook/marketplace/listing",
            _params(("listing_id", listing_id), extra=kwargs),
        ).json()

    def get_seller_details(self, seller_id: str, **kwargs: Any) -> dict[str, Any]:
        """Return seller profile, ratings, reviews, and badges from
        Marketplace.

        Backed by ``GET /facebook/marketplace/seller``.
        """
        return self._get(
            "/facebook/marketplace/seller",
            _params(("seller_id", seller_id), extra=kwargs),
        ).json()

    def get_marketplace_categories(self, **kwargs: Any) -> dict[str, Any]:
        """Return all Marketplace categories with SEO URLs and IDs.

        Backed by ``GET /facebook/marketplace/categories``.
        """
        return self._get(
            "/facebook/marketplace/categories",
            _params(extra=kwargs),
        ).json()

    def get_city_coordinates(self, city: str, **kwargs: Any) -> dict[str, Any]:
        """Resolve a city name to GPS coordinates, for use as a
        Marketplace location filter.

        Backed by ``GET /facebook/marketplace/city-coordinates``. Pass
        ``exactly_one="true"`` to return the top match only.
        """
        return self._get(
            "/facebook/marketplace/city-coordinates",
            _params(("city", city), extra=kwargs),
        ).json()

    def search_vehicles(self, **kwargs: Any) -> dict[str, Any]:
        """Search Marketplace vehicle listings.

        Backed by ``GET /facebook/marketplace/vehicles``. Required-ish
        params: ``filter_location_latitude`` + ``filter_location_longitude``.
        """
        return self._get(
            "/facebook/marketplace/vehicles",
            _params(extra=kwargs),
        ).json()

    def search_rentals(self, **kwargs: Any) -> dict[str, Any]:
        """Search Marketplace rental-property listings.

        Backed by ``GET /facebook/marketplace/rentals``. Filters:
        ``filter_bedrooms_min``, ``filter_bathrooms_min``,
        ``filter_price_max``, plus the location lat/lng.
        """
        return self._get(
            "/facebook/marketplace/rentals",
            _params(extra=kwargs),
        ).json()

    # =======================================================================
    # MEDIA
    # =======================================================================

    def download_media(self, url: str, **kwargs: Any) -> dict[str, Any]:
        """Resolve a Facebook video/photo URL to a direct downloadable
        media URL.

        Backed by ``GET /facebook/media/download``.
        """
        return self._get(
            "/facebook/media/download",
            _params(("url", url), extra=kwargs),
        ).json()

    # =======================================================================
    # INTERNAL: shared request driver
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
class AsyncFacebook(BaseClient):
    """Asynchronous Facebook client. Same method shape as :class:`Facebook`,
    but every public method is a coroutine.

    Quick start::

        from socialapis import AsyncFacebook

        async with AsyncFacebook(api_token="YOUR_API_TOKEN") as fb:
            page = await fb.get_page_info("EngenSA")
            posts = await fb.get_page_posts("EngenSA")
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

    # =======================================================================
    # PAGES
    # =======================================================================

    async def get_page_id(self, page: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/pages/id",
                _params(("link", _as_facebook_url(page)), extra=kwargs),
            )
        ).json()

    async def get_page_info(self, page: str, **kwargs: Any) -> PageInfo:
        response = await self._get(
            "/facebook/pages/details",
            _params(("link", _as_facebook_url(page)), extra=kwargs),
        )
        return PageInfo.model_validate(response.json())

    async def get_page_posts(self, page: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/pages/posts",
                _params(("link", _as_facebook_url(page)), extra=kwargs),
            )
        ).json()

    async def get_page_reels(self, page: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/pages/reels",
                _params(("link", _as_facebook_url(page)), extra=kwargs),
            )
        ).json()

    async def get_page_videos(self, page: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/pages/videos",
                _params(("link", _as_facebook_url(page)), extra=kwargs),
            )
        ).json()

    # =======================================================================
    # GROUPS
    # =======================================================================

    async def get_group_id(self, group: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/groups/id",
                _params(("link", _as_facebook_group_url(group)), extra=kwargs),
            )
        ).json()

    async def get_group_details(self, group: str, **kwargs: Any) -> GroupInfo:
        response = await self._get(
            "/facebook/groups/details",
            _params(("link", _as_facebook_group_url(group)), extra=kwargs),
        )
        return GroupInfo.model_validate(response.json())

    async def get_group_metadata(self, group: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/groups/metadata",
                _params(("link", _as_facebook_group_url(group)), extra=kwargs),
            )
        ).json()

    async def get_group_posts(self, group: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/groups/posts",
                _params(("link", _as_facebook_group_url(group)), extra=kwargs),
            )
        ).json()

    async def get_group_videos(self, group_id: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/groups/videos",
                _params(("group_id", group_id), extra=kwargs),
            )
        ).json()

    # =======================================================================
    # POSTS
    # =======================================================================

    async def get_post_id(self, post: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/posts/id",
                _params(("link", post), extra=kwargs),
            )
        ).json()

    async def get_post_details(self, post: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/posts/details",
                _params(("link", post), extra=kwargs),
            )
        ).json()

    async def get_post_details_extended(self, post: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/posts/details/extended",
                _params(("link", post), extra=kwargs),
            )
        ).json()

    async def get_post_comments(self, post: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/posts/comments",
                _params(("link", post), extra=kwargs),
            )
        ).json()

    async def get_comment_replies(
        self,
        comment_feedback_id: str,
        expansion_token: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/posts/comments/replies",
                _params(
                    ("comment_feedback_id", comment_feedback_id),
                    ("expansion_token", expansion_token),
                    extra=kwargs,
                ),
            )
        ).json()

    async def get_post_attachments(self, post_id: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/posts/attachments",
                _params(("post_id", post_id), extra=kwargs),
            )
        ).json()

    async def get_video_post_details(self, video_id: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/posts/video",
                _params(("video_id", video_id), extra=kwargs),
            )
        ).json()

    # =======================================================================
    # SEARCH
    # =======================================================================

    async def search_pages(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/search/pages",
                _params(("query", query), extra=kwargs),
            )
        ).json()

    async def search_people(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/search/people",
                _params(("query", query), extra=kwargs),
            )
        ).json()

    async def search_locations(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/search/locations",
                _params(("query", query), extra=kwargs),
            )
        ).json()

    async def search_posts(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/search/posts",
                _params(("query", query), extra=kwargs),
            )
        ).json()

    async def search_videos(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/search/videos",
                _params(("query", query), extra=kwargs),
            )
        ).json()

    # =======================================================================
    # ADS LIBRARY
    # =======================================================================

    async def get_ads_countries(self, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/ads/countries",
                _params(extra=kwargs),
            )
        ).json()

    async def search_ads(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/ads/search",
                _params(("query", query), extra=kwargs),
            )
        ).json()

    async def get_ads_page_details(self, page_id: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/ads/page-details",
                _params(("page_id", page_id), extra=kwargs),
            )
        ).json()

    async def get_ad_archive_details(
        self,
        ad_archive_id: str,
        page_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/ads/archive-details",
                _params(
                    ("ad_archive_id", ad_archive_id),
                    ("page_id", page_id),
                    extra=kwargs,
                ),
            )
        ).json()

    async def search_ads_by_keywords(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/ads/keywords",
                _params(("query", query), extra=kwargs),
            )
        ).json()

    # =======================================================================
    # MARKETPLACE
    # =======================================================================

    async def search_marketplace(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/marketplace/search",
                _params(("query", query), extra=kwargs),
            )
        ).json()

    async def get_listing_details(self, listing_id: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/marketplace/listing",
                _params(("listing_id", listing_id), extra=kwargs),
            )
        ).json()

    async def get_seller_details(self, seller_id: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/marketplace/seller",
                _params(("seller_id", seller_id), extra=kwargs),
            )
        ).json()

    async def get_marketplace_categories(self, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/marketplace/categories",
                _params(extra=kwargs),
            )
        ).json()

    async def get_city_coordinates(self, city: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/marketplace/city-coordinates",
                _params(("city", city), extra=kwargs),
            )
        ).json()

    async def search_vehicles(self, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/marketplace/vehicles",
                _params(extra=kwargs),
            )
        ).json()

    async def search_rentals(self, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/marketplace/rentals",
                _params(extra=kwargs),
            )
        ).json()

    # =======================================================================
    # MEDIA
    # =======================================================================

    async def download_media(self, url: str, **kwargs: Any) -> dict[str, Any]:
        return (
            await self._get(
                "/facebook/media/download",
                _params(("url", url), extra=kwargs),
            )
        ).json()

    # =======================================================================
    # INTERNAL
    # =======================================================================

    async def _get(self, path: str, params: dict[str, str]) -> httpx.Response:
        url = self._build_url(path)
        try:
            response = await self._transport.get(url, params=params)
        except httpx.RequestError as exc:
            raise APIConnectionError(f"Request failed: {exc}") from exc
        self._raise_for_status(response)
        return response
