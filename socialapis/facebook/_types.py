"""Pydantic v2 response models for the Facebook namespace.

Why Pydantic v2 over dataclasses or plain dicts:
- Runtime validation — the API can drift; we want a loud error, not silent
  `None` dereferences five lines later.
- IDE autocomplete on every field.
- `model_extra` config means new fields the API adds don't break old clients
  (they land on the model untouched; callers using `.model_dump()` see them).
- Pydantic v2 is Rust-backed — fast enough that runtime validation is free.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class _Model(BaseModel):
    """Shared base for every response model.

    `extra="allow"` means the API can ADD fields without breaking existing
    integrations. Old fields can be removed without breaking too (the
    attribute just becomes `None`-equivalent on access — see individual
    field types).

    `populate_by_name=True` lets us alias API field names to Pythonic ones
    without losing the API name (relevant when the API uses camelCase or
    weird casings).
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class PageInfo(_Model):
    """Public metadata returned by `Facebook.get_page_info()`.

    Backed by `GET /v1/facebook/page/details`. Only fields the API
    consistently returns are typed; everything else lands in `model_extra`
    and is accessible via `.model_dump()` for forward-compat.
    """

    id: str = Field(description="Facebook's internal page identifier.")
    name: str | None = Field(default=None, description="Display name of the page.")
    url: str | None = Field(default=None, description="Canonical Facebook URL.")
    category: str | None = Field(default=None, description="Page category, e.g. 'Public figure'.")
    likes: int | None = Field(default=None, description="Cumulative like count, when available.")
    followers: int | None = Field(default=None, description="Follower count.")
    verified: bool | None = Field(default=None, description="Whether the page has a blue checkmark.")
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
