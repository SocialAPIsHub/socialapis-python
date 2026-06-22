"""Public sync + async Facebook clients.

Pattern: thin method-per-endpoint wrappers over the internal BaseClient.
Each method:
    1. Validates the input shape (let httpx + pydantic raise on bad data)
    2. Builds the URL + query params
    3. Issues the HTTP call (sync or async)
    4. Maps the response into a typed Pydantic model
    5. Lets typed exceptions from BaseClient propagate cleanly

The sync and async classes share method signatures so callers can swap
between them by renaming one import line.
"""

from __future__ import annotations

from types import TracebackType
from typing import TYPE_CHECKING

import httpx

from .._client import BaseClient
from .._errors import APIConnectionError
from ._types import PageInfo

if TYPE_CHECKING:
    from typing import Self


def _normalize_page_query(page: str) -> dict[str, str]:
    """The /facebook/page/details endpoint accepts EITHER a full URL OR a
    username/slug — we let the caller pass whichever and normalize to the
    `link` query param the API expects.

    Examples:
        "EngenSA"                              → link=https://www.facebook.com/EngenSA
        "https://www.facebook.com/EngenSA"     → link=https://www.facebook.com/EngenSA
        "https://m.facebook.com/EngenSA"       → link=https://m.facebook.com/EngenSA
    """
    if not page:
        raise ValueError("page is required (Facebook username, slug, or full URL)")
    page = page.strip()
    if page.startswith("http://") or page.startswith("https://"):
        return {"link": page}
    # Bare username/slug — prepend the canonical Facebook URL
    return {"link": f"https://www.facebook.com/{page}"}


# ============================================================================
# SYNC CLIENT
# ============================================================================
class Facebook(BaseClient):
    """Synchronous Facebook client.

    Drop-in alternative to the abandoned kevinzg/facebook-scraper library.
    All public-data calls route through socialapis.io — no OAuth, no
    Facebook app review, no scraper maintenance.

    Quick start:
        from socialapis import Facebook

        fb = Facebook(api_token="sk_live_...")  # or use `with`
        page = fb.get_page_info("EngenSA")
        print(page.name, page.likes)
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
        # The transport kwarg is primarily for tests (respx-mocked client).
        # In production code, callers don't need to construct it themselves.
        self._transport = transport or httpx.Client(
            timeout=self.timeout,
            headers=self._default_headers(),
        )
        self._owns_transport = transport is None

    # ---- context-manager interface (recommended usage) ----------------------

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
        """Close the underlying connection pool. Safe to call multiple times."""
        if self._owns_transport:
            self._transport.close()

    # ---- API methods --------------------------------------------------------

    def get_page_info(self, page: str) -> PageInfo:
        """Return public metadata for a Facebook Page.

        Backed by `GET /v1/facebook/page/details`.

        Args:
            page: Either a Facebook page slug (e.g. ``"EngenSA"``) or a full
                URL (e.g. ``"https://www.facebook.com/EngenSA"``). The SDK
                normalizes either form.

        Returns:
            A :class:`PageInfo` model with typed fields for name, category,
            likes, followers, etc. Fields the API didn't return are ``None``;
            new fields the API adds are preserved on ``model_extra``.

        Raises:
            AuthenticationError: If the API token is invalid.
            InsufficientCreditsError: If the account has no remaining credits.
            RateLimitError: If the per-key rate limit was exceeded.
            BadRequestError: If the page URL is malformed or the page doesn't exist.
            APIServerError: If the upstream API returned a 5xx.
            APIConnectionError: If the request couldn't reach the API at all.
        """
        params = _normalize_page_query(page)
        response = self._request("GET", "/v1/facebook/page/details", params=params)
        return PageInfo.model_validate(response.json())

    # ---- internal: shared request driver ------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
    ) -> httpx.Response:
        url = self._build_url(path)
        try:
            response = self._transport.request(method, url, params=params)
        except httpx.RequestError as exc:
            raise APIConnectionError(f"Request failed: {exc}") from exc
        self._raise_for_status(response)
        return response


# ============================================================================
# ASYNC CLIENT
# ============================================================================
class AsyncFacebook(BaseClient):
    """Asynchronous Facebook client.

    Same method shape as :class:`Facebook` — methods are coroutines.

    Quick start:
        from socialapis import AsyncFacebook

        async with AsyncFacebook(api_token="sk_live_...") as fb:
            page = await fb.get_page_info("EngenSA")
            print(page.name, page.likes)
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
        """Close the underlying async connection pool. Safe to call repeatedly."""
        if self._owns_transport:
            await self._transport.aclose()

    async def get_page_info(self, page: str) -> PageInfo:
        """Async variant of :meth:`Facebook.get_page_info`. Same semantics."""
        params = _normalize_page_query(page)
        response = await self._request("GET", "/v1/facebook/page/details", params=params)
        return PageInfo.model_validate(response.json())

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
    ) -> httpx.Response:
        url = self._build_url(path)
        try:
            response = await self._transport.request(method, url, params=params)
        except httpx.RequestError as exc:
            raise APIConnectionError(f"Request failed: {exc}") from exc
        self._raise_for_status(response)
        return response
