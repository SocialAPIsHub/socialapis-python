"""Pydantic v2 response models for the Instagram namespace.

Same design as the Facebook namespace: hand-typed model for the headline
endpoint (ProfileInfo from `get_profile_details`), `dict[str, Any]`
returns for the niche endpoints, every model uses `extra="allow"` so
new API fields don't break old callers.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class _Model(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class ProfileInfo(_Model):
    """Public Instagram profile metadata.

    Backed by ``GET /instagram/profile/details``. The fields below are the
    common ones; anything else the API returns is preserved on
    ``model_extra``.
    """

    id: str | None = None
    username: str | None = None
    full_name: str | None = Field(default=None, alias="fullName")
    biography: str | None = None
    followers: int | None = Field(default=None, alias="followerCount")
    following: int | None = Field(default=None, alias="followingCount")
    posts_count: int | None = Field(default=None, alias="postsCount")
    is_verified: bool | None = Field(default=None, alias="isVerified")
    is_private: bool | None = Field(default=None, alias="isPrivate")
    is_business: bool | None = Field(default=None, alias="isBusiness")
    profile_picture_url: str | None = Field(default=None, alias="profilePictureUrl")
    external_url: str | None = Field(default=None, alias="externalUrl")
    category: str | None = None
