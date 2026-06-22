"""Pydantic v2 response models for the Facebook namespace.

All models use `extra="allow"` so the API can ADD fields without breaking
us. Field names below mirror the EXACT field names the live API returns
(verified against a real token, 2026-06-22). Anything else lands in
`model_extra` and is accessible via `.model_dump()` for forward-compat.

The niche endpoints (Ads Library archive details, Marketplace city
coordinates, etc.) return plain `dict[str, Any]` to keep the SDK
shipping fast — callers who want type safety can build wrappers
themselves.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class _Model(BaseModel):
    """Shared base for every response model.

    Forward-compatible by default — API can add fields without breaking us,
    and any unrecognised fields land in model_extra (accessible via
    .model_dump()) so callers never lose data.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class PageInfo(_Model):
    """Public metadata returned by `Facebook.get_page_info()`.

    Backed by `GET /facebook/pages/details`. The API wraps this payload
    under a string key `"0"` in the response envelope — the SDK
    unwraps that before validation.

    Field names match the live API exactly. Most fields are optional
    because the API populates them only when the page provides them
    (e.g. a personal page won't have business_hours).
    """

    # Identifiers
    ad_page_id: str | None = None
    user_id: str | None = None

    # Display
    title: str | None = None
    url: str | None = None
    category: list[str] | str | None = None
    status: str | None = None

    # Content
    bio: str | None = None
    description: str | None = None

    # Contact
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    maps_address: str | None = None

    # Engagement (the API exposes both `_count` (int) and `_display` (str))
    followers_count: int | None = None
    followers_display: str | None = None
    likes_count: int | None = None
    likes_display: str | None = None

    # Media
    image: str | None = None
    image_alt: str | None = None

    # Ratings
    rating: str | None = None
    rating_count: int | None = None
    rating_overall: str | None = None

    # Business hours / pricing (often None for non-business pages)
    business_hours: str | None = None
    business_price: str | None = None
    business_services: str | None = None
    is_business_page_active: bool | None = None
    confirmed_owner_label: str | None = None

    # Linked social accounts
    twitter: str | None = None
    instagram: str | None = None
    linkedin: str | None = None
    pinterest: str | None = None
    telegram: str | None = None
    youtube: str | None = None


class GroupInfo(_Model):
    """Public metadata for a Facebook Group. Backed by `GET /facebook/groups/details`.

    NOTE: this endpoint has NO envelope — the payload sits at the top level
    of the response (alongside `message` and `meta`). The SDK passes the
    raw body straight to this model.
    """

    group_id: str | None = None
    group_member_count: str | None = None
    group_total_members_info_text: str | None = None
    group_new_members_info_text: str | None = None
    description_text: str | None = None
    privacy_info_text: dict | None = None
    created_time: int | None = None
    group_rules: list | None = None
    group_history: dict | None = None
    admin_tags: list | None = None
    group_locations: list | None = None
    number_of_posts_in_last_day: int | None = None
    number_of_posts_in_last_month: int | None = None
