# Changelog

All notable changes to this project will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] — 2026-06-22

### Fixed (breaking for the typed-model methods)

- **`Facebook.get_page_info` / `AsyncFacebook.get_page_info`** now correctly
  unwrap the API's response envelope. The endpoint returns
  `{"0": {...payload}, "message": ..., "meta": ...}` — v0.1.0 passed the
  whole envelope to `PageInfo.model_validate()`, which left every typed
  attribute as `None`. v0.1.1 extracts the `"0"` key before validation.
- **`Instagram.get_profile_details` / `AsyncInstagram.get_profile_details`**
  same fix — the endpoint wraps the payload under `"data"` (with sibling
  `"success"`, `"message"`, `"meta"`); v0.1.0 didn't unwrap.
- **`PageInfo`** rewritten with the real field names the API returns
  (`ad_page_id`, `user_id`, `title`, `category`, `bio`, `description`,
  `followers_count`, `likes_count`, `image`, `rating`, `business_hours`,
  `twitter`/`instagram`/`linkedin`/`pinterest`/`telegram`/`youtube`, etc.).
  Removed v0.1.0's invented fields (`name`, `likes`, `verified`,
  `profile_image_url`) — they never populated against real responses.
- **`GroupInfo`** rewritten with the real field names
  (`group_id`, `group_member_count`, `description_text`,
  `created_time`, `group_rules`, `number_of_posts_in_last_day`, etc.).
- **`ProfileInfo`** rewritten with the real Instagram field names
  (`id`, `pk`, `fbid`, `full_name`, `followers_count`, `following_count`,
  `media_count`, `is_verified`, `profile_pic_url`, etc.). Removed v0.1.0's
  invented `posts_count`, `follower_count` (singular) aliases.

### Why this is a breaking change

If any code was reading `page.likes`, `page.name`, `profile.followers`,
`profile.posts_count`, those will now raise `AttributeError`. v0.1.0 left
all those attributes as `None` (because the envelope was never unwrapped),
so any code that checked for them was already not getting real data — but
the rename is still technically breaking.

Discovered via a real-API smoke test (added in
`scripts/integration_smoke.py`). Every other endpoint method that returns
`dict[str, Any]` was unaffected — those already pass through the raw
response.

### Unchanged

- Public import paths (`from socialapis import Facebook, Instagram, ...`)
- All wire-level behaviour (URLs, headers, query params)
- The typed exception hierarchy (`AuthenticationError`,
  `RateLimitError`, etc.)
- The migration aliases (`FacebookScraper`, `InstagramScraper`)

## [0.1.0] — 2026-06-22

First public release. Full coverage of the SocialAPIs.io public REST surface
in one shot — no v0.2/v0.3 follow-ups required for core endpoints.

> **PyPI distribution name**: `socialapis-sdk` (install with
> `pip install socialapis-sdk`). The Python import path is the
> shorter `socialapis` (`from socialapis import Facebook`) — those
> two are independent on PyPI.

### Added — Facebook namespace (`Facebook` / `AsyncFacebook`)

**Pages**: `get_page_id`, `get_page_info`, `get_page_posts`, `get_page_reels`,
`get_page_videos`

**Groups**: `get_group_id`, `get_group_details`, `get_group_metadata`,
`get_group_posts`, `get_group_videos`

**Posts**: `get_post_id`, `get_post_details`, `get_post_details_extended`,
`get_post_comments`, `get_comment_replies`, `get_post_attachments`,
`get_video_post_details`

**Search**: `search_pages`, `search_people`, `search_locations`,
`search_posts`, `search_videos`

**Meta Ads Library**: `get_ads_countries`, `search_ads`,
`get_ads_page_details`, `get_ad_archive_details`, `search_ads_by_keywords`

**Marketplace**: `search_marketplace`, `get_listing_details`,
`get_seller_details`, `get_marketplace_categories`, `get_city_coordinates`,
`search_vehicles`, `search_rentals`

**Media**: `download_media`

### Added — Instagram namespace (`Instagram` / `AsyncInstagram`)

**Profiles**: `get_user_id`, `get_profile_details`, `get_profile_posts`,
`get_profile_reels`, `get_profile_highlights`, `get_highlight_details`

**Posts**: `get_post_id`, `get_post_details`

**Reels**: `get_reels_feed`, `get_reels_by_audio`

**Search + Locations**: `search`, `get_location_posts`,
`get_nearby_locations`

### Added — Account namespace (`Account` / `AsyncAccount`)

`get_usage`, `get_top_ups`, `get_limits`. All free (don't consume credits).

### Added — Infrastructure

- Typed exception hierarchy (`SocialAPIsError`, `APIError`,
  `AuthenticationError`, `InsufficientCreditsError`, `RateLimitError`,
  `BadRequestError`, `APIServerError`, `APIConnectionError`)
- Pydantic v2 response models for headline endpoints (`PageInfo`,
  `GroupInfo`, `ProfileInfo`). Niche endpoints return `dict[str, Any]`
  with full data preserved.
- Sync + async context-manager support (`with` / `async with`)
- Identifier normalisation — pass either a slug or a full URL; the SDK
  coerces to whatever shape the API expects
- `**kwargs` pass-through on every method — forward-compatible when the
  API adds new filters; no client release needed to use them
- No `limit=N` parameters anywhere — the API decides page size; pagination
  is cursor-driven via response body + kwargs

### Added — Migration aliases (graveyard capture)

- `FacebookScraper` / `AsyncFacebookScraper` — exact aliases of
  `Facebook` / `AsyncFacebook`. Lets users of the abandoned
  `kevinzg/facebook-scraper` library migrate by changing only the import.
- `InstagramScraper` / `AsyncInstagramScraper` — same for users of
  `arc298/instagram-scraper`.
- `test_aliases.py` asserts the identity contract so accidental
  decoupling fails CI.

### Added — Tooling

- `pyproject.toml` with hatchling, modern Python (3.10+), no `setup.py`
- Test suite using `respx` for HTTP mocking (no live API calls in CI)
- CI: lint (ruff), type check (mypy --strict), tests on Python 3.10–3.13
- Release workflow: publishes to PyPI via Trusted Publishing on
  `vX.Y.Z` tag (no API token to rotate)
- PEP 561 `py.typed` marker — distributed type hints
- Coverage gate at 85% in CI
