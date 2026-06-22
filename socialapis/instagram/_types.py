"""Pydantic v2 response models for the Instagram namespace.

Same design as the Facebook namespace: hand-typed model for the headline
endpoint (ProfileInfo from `get_profile_details`), `dict[str, Any]`
returns for the niche endpoints, every model uses `extra="allow"` so
new API fields don't break old callers.

Field names match the live API exactly (verified against a real token,
2026-06-22).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class _Model(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class ProfileInfo(_Model):
    """Public Instagram profile metadata.

    Backed by `GET /instagram/profile/details`. The API wraps the payload
    under the key `"data"` in the envelope (alongside `success`, `message`,
    `meta`) — the SDK unwraps that before validation.

    Fields below match the live API's field names exactly.
    """

    # Identifiers
    id: str | None = None
    pk: str | None = None
    fbid: str | None = None

    # Display
    username: str | None = None
    full_name: str | None = None
    biography: str | None = None
    category_name: str | None = None

    # Media URLs
    profile_pic_url: str | None = None
    profile_pic_url_hd: str | None = None
    external_url: str | None = None
    external_url_linkshimmed: str | None = None

    # Counts
    followers_count: int | None = None
    following_count: int | None = None
    media_count: int | None = None
    total_clips_count: int | None = None
    highlight_reel_count: int | None = None
    mutual_followers_count: int | None = None

    # Flags
    is_private: bool | None = None
    is_verified: bool | None = None
    is_business_account: bool | None = None
    is_professional_account: bool | None = None
    is_memorialized: bool | None = None
    is_unpublished: bool | None = None
    is_embeds_disabled: bool | None = None
    is_joined_recently: bool | None = None
    is_regulated_c18: bool | None = None
    account_type: int | None = None

    # Features the profile has enabled
    has_clips: bool | None = None
    has_guides: bool | None = None
    has_channel: bool | None = None
    has_ar_effects: bool | None = None

    # Business contact (often None for personal accounts)
    business_category_name: str | None = None
    business_email: str | None = None
    business_phone_number: str | None = None
    business_contact_method: str | None = None
    address_street: str | None = None
    city_name: str | None = None
    zip: str | None = None

    # Misc
    pronouns: list | None = None
    account_badges: list | None = None
