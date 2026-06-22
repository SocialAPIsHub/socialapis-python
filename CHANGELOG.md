# Changelog

All notable changes to this project will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — Unreleased

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
