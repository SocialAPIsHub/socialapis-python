# Changelog

All notable changes to this project will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial scaffolding — `Facebook` (sync) and `AsyncFacebook` (async) clients
- First public method: `get_page_info(page)` — returns a typed `PageInfo`
  Pydantic model
- Typed exception hierarchy: `SocialAPIsError`, `APIError`,
  `AuthenticationError`, `InsufficientCreditsError`, `RateLimitError`,
  `BadRequestError`, `APIServerError`, `APIConnectionError`
- Sync + async context-manager support (`with` / `async with`)
- Test suite using `respx` for HTTP mocking (no live API calls in CI)
- CI: lint (ruff), type check (mypy --strict), tests on Python 3.10–3.13
- Release workflow: publishes to PyPI via Trusted Publishing on `vX.Y.Z` tag

## [0.1.0] — unreleased

First public release — foundation only. See "Unreleased" above.
Subsequent releases will add the rest of the Facebook surface
(get_posts, get_group_details, search_pages, search_posts, ads library,
marketplace) and the Instagram namespace.
