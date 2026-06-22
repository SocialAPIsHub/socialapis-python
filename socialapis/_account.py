"""Account-level endpoints — usage, credits, rate-limit info.

Different from the Facebook / Instagram namespaces because these calls are
about YOUR socialapis.io account, not about scraped data. They don't
consume credits (free to call) and they're useful for paid integrations
that want to monitor their own budget programmatically.

Exposed at the package top-level via ``socialapis.Account``.
"""

from __future__ import annotations

from types import TracebackType
from typing import TYPE_CHECKING, Any

import httpx

from ._client import BaseClient
from ._errors import APIConnectionError

if TYPE_CHECKING:
    from typing import Self


class Account(BaseClient):
    """Synchronous account-info client. None of these calls consume credits.

    Quick start::

        from socialapis import Account

        with Account(api_token="YOUR_API_TOKEN") as acc:
            usage = acc.get_usage()
            print(usage["credits"]["remaining"])
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

    def get_usage(self) -> dict[str, Any]:
        """Return current credit balance, usage, plan info, billing period.

        Backed by ``GET /usage``. Free — does not consume credits.
        """
        return self._get("/usage").json()

    def get_top_ups(self) -> dict[str, Any]:
        """Return auto top-up settings + recent history + lifetime spend.

        Backed by ``GET /usage/top-ups``. Free.
        """
        return self._get("/usage/top-ups").json()

    def get_limits(self) -> dict[str, Any]:
        """Return your plan's rate limit, concurrent-task cap, and allowed
        top-up packages.

        Backed by ``GET /usage/limits``. Free.
        """
        return self._get("/usage/limits").json()

    def _get(self, path: str) -> httpx.Response:
        url = self._build_url(path)
        try:
            response = self._transport.get(url)
        except httpx.RequestError as exc:
            raise APIConnectionError(f"Request failed: {exc}") from exc
        self._raise_for_status(response)
        return response


class AsyncAccount(BaseClient):
    """Asynchronous account-info client. Same surface as :class:`Account`;
    every method is a coroutine.
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

    async def get_usage(self) -> dict[str, Any]:
        return (await self._get("/usage")).json()

    async def get_top_ups(self) -> dict[str, Any]:
        return (await self._get("/usage/top-ups")).json()

    async def get_limits(self) -> dict[str, Any]:
        return (await self._get("/usage/limits")).json()

    async def _get(self, path: str) -> httpx.Response:
        url = self._build_url(path)
        try:
            response = await self._transport.get(url)
        except httpx.RequestError as exc:
            raise APIConnectionError(f"Request failed: {exc}") from exc
        self._raise_for_status(response)
        return response
