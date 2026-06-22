"""Pydantic v2 response models for the Facebook namespace.

Design decision: we hand-craft typed models for a small set of "headline"
endpoints (PageInfo, GroupInfo, PostDetails, ProfileDetails) where IDE
autocomplete is most valuable. The niche endpoints (Ads Library archive
details, Marketplace city coordinates, etc.) return plain `dict[str, Any]`
to keep the SDK shipping fast — callers who care can build typed wrappers
themselves.

Every typed model uses `extra="allow"` so the API can ADD fields without
breaking existing integrations. Old fields can be removed; the attribute
just goes None.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


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

    Backed by `GET /facebook/pages/details`. Common fields typed for
    autocomplete; anything else the API returns is preserved in
    `model_extra`.
    """

    id: str | None = Field(default=None, description="Facebook's internal page identifier.")
    name: str | None = Field(default=None, description="Display name of the page.")
    url: str | None = Field(default=None, description="Canonical Facebook URL.")
    category: str | None = Field(default=None, description="Page category, e.g. 'Public figure'.")
    likes: int | None = Field(default=None, description="Cumulative like count, when available.")
    followers: int | None = Field(default=None, description="Follower count.")
    verified: bool | None = Field(
        default=None, description="Whether the page has a blue checkmark."
    )
    about: str | None = Field(default=None, description="Free-text 'About' description.")
    website: str | None = Field(default=None, description="Linked external website, when present.")
    profile_image_url: str | None = Field(
        default=None,
        description="URL to the page's profile image.",
        alias="profileImageUrl",
    )
    cover_image_url: str | None = Field(
        default=None,
        description="URL to the page's cover image.",
        alias="coverImageUrl",
    )


class GroupInfo(_Model):
    """Public metadata for a Facebook Group. Backed by `GET /facebook/groups/details`."""

    id: str | None = None
    name: str | None = None
    url: str | None = None
    description: str | None = None
    member_count: int | None = Field(default=None, alias="memberCount")
    privacy: str | None = None
    is_public: bool | None = Field(default=None, alias="isPublic")
