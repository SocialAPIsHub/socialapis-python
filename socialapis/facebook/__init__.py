"""Facebook namespace.

Public entry points:
    socialapis.Facebook       — synchronous client
    socialapis.AsyncFacebook  — asyncio client

Both share the same method signatures; only the call pattern differs.

    sync:
        from socialapis import Facebook
        fb = Facebook(api_token="...")
        page = fb.get_page_info("EngenSA")

    async:
        from socialapis import AsyncFacebook
        async with AsyncFacebook(api_token="...") as fb:
            page = await fb.get_page_info("EngenSA")
"""

from ._client import AsyncFacebook, Facebook
from ._types import PageInfo

__all__ = ["AsyncFacebook", "Facebook", "PageInfo"]
