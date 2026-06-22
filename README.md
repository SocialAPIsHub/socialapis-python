# socialapis — Python SDK for Facebook + Instagram public data

[![PyPI](https://img.shields.io/pypi/v/socialapis.svg)](https://pypi.org/project/socialapis/)
[![Python versions](https://img.shields.io/pypi/pyversions/socialapis.svg)](https://pypi.org/project/socialapis/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

The modern alternative to [`kevinzg/facebook-scraper`](https://github.com/kevinzg/facebook-scraper)
and [`arc298/instagram-scraper`](https://github.com/arc298/instagram-scraper) —
real-time Facebook + Instagram data via REST, **no OAuth dance, no app
review, no scraper maintenance**. Powered by hosted infrastructure at
[socialapis.io](https://socialapis.io).

```bash
pip install socialapis
```

```python
from socialapis import Facebook

fb = Facebook(api_token="...")
page = fb.get_page_info("EngenSA")
print(page.name, page.likes, page.category)
```

**[Get a free API token →](https://socialapis.io/auth/signup)** (200 calls/month, no credit card)

## One-line migration from `facebook-scraper`

If your code currently uses [`kevinzg/facebook-scraper`](https://github.com/kevinzg/facebook-scraper), the migration is **literally one line**:

```python
# Before — kevinzg/facebook-scraper (abandoned since 2022)
from facebook_scraper import get_posts

# After — socialapis (drop-in alias preserves the call name)
from socialapis import FacebookScraper       # alias of `Facebook`
fb = FacebookScraper(api_token="...")
```

The `FacebookScraper` alias exists so migrations stay greppable. Method
names match too — `get_page_info`, `get_posts`, etc. (see the migration
table further down).

---

## Why this exists

`kevinzg/facebook-scraper` has 9.5k+ GitHub stars and was the default
Python library for scraping Facebook for years. It's been **abandoned since
2022** — every Facebook DOM change breaks it, the fixes pile up in
unmerged PRs, and downloads drift to forks that fix one bug and break two.

This SDK is a **drop-in successor** that talks to a hosted API instead.
You get:

| | `kevinzg/facebook-scraper` (2018-era) | `socialapis` (2026) |
|---|---|---|
| **Maintenance** | Abandoned 2022 | Active; we run prod for 7M+ calls/mo |
| **Reliability** | Breaks on every Meta HTML change | Hosted backend; we absorb breakage |
| **Type hints** | None | Strict throughout |
| **Async support** | No | `Facebook` + `AsyncFacebook` classes |
| **HTTP client** | `requests` | `httpx` |
| **Validation** | Manual dict parsing | Pydantic v2 models |
| **Auth** | None (scrapes anonymously) | Single `x-api-token` header |
| **Pagination** | Generator with edge-case bugs | Clean iterator + cursor handling |
| **Error handling** | Generic exceptions | Typed hierarchy (`RateLimitError`, etc.) |
| **CI / tests** | Manual against live FB | Recorded HTTP fixtures, Python 3.10–3.13 |

The trade-off: instead of running a scraper yourself, you make a REST call
to our hosted API. **200 calls/month free**, no credit card. Paid plans
start at $4.99/mo for 1,500 calls.

## Quick start

### 1. Get an API token

[Sign up free at socialapis.io](https://socialapis.io/auth/signup) — 200 calls/month, no credit card.

### 2. Install

```bash
pip install socialapis
```

Requires Python 3.10+.

### 3. Make your first call

```python
from socialapis import Facebook

fb = Facebook(api_token="sk_live_...")

page = fb.get_page_info("EngenSA")
print(page.name)              # "Engen SA"
print(page.category)          # "Petroleum Service"
print(page.likes)             # 1234567
print(page.verified)          # True
print(page.profile_image_url) # "https://scontent.fbcdn.net/..."
```

The return value is a typed [Pydantic](https://docs.pydantic.dev/) model —
your IDE will autocomplete every field. New fields the API adds in future
versions are preserved on `model_extra` for forward compatibility.

### 4. Use the async client when you have many calls

```python
import asyncio
from socialapis import AsyncFacebook

async def main():
    async with AsyncFacebook(api_token="sk_live_...") as fb:
        pages = await asyncio.gather(*[
            fb.get_page_info(slug)
            for slug in ["EngenSA", "Microsoft", "GitHub"]
        ])
        for page in pages:
            print(page.name, page.followers)

asyncio.run(main())
```

## Migrating from `kevinzg/facebook-scraper`

Methods map approximately 1-to-1, with cleaner typed returns:

| `kevinzg/facebook-scraper` | `socialapis` |
|---|---|
| `from facebook_scraper import get_page_info` | `from socialapis import FacebookScraper` |
| `get_page_info("page")` | `FacebookScraper(api_token=...).get_page_info("page")` |
| `get_posts("page", pages=N)` | `FacebookScraper(...).get_posts("page", limit=N)` *(v0.2)* |
| `get_group_info("group")` | `FacebookScraper(...).get_group_details("group")` *(v0.2)* |
| `get_friends("user")` | (Meta blocked it years ago — even kevinzg deprecated it) |
| `set_proxy(...)` / `set_user_agent(...)` | Not needed — we manage the infra |
| `set_cookies(...)` | Not needed — no login required |

Full working migration example:
[`examples/migrate-from-kevinzg.py`](examples/migrate-from-kevinzg.py)

The remaining method surface ships across subsequent releases (v0.2, v0.3).
Track progress in [CHANGELOG.md](CHANGELOG.md).

## Error handling

```python
import time
from socialapis import (
    Facebook,
    AuthenticationError,           # 401 — bad token
    InsufficientCreditsError,      # 402 — out of credits
    RateLimitError,                # 429 — slow down
    BadRequestError,               # 4xx — bad input
    APIServerError,                # 5xx — retry safely
    APIConnectionError,            # network — retry with backoff
)

fb = Facebook(api_token="...")
try:
    page = fb.get_page_info("EngenSA")
except RateLimitError as exc:
    time.sleep(exc.retry_after_seconds or 5)
    page = fb.get_page_info("EngenSA")
except InsufficientCreditsError:
    print("Out of credits. Upgrade at https://socialapis.io/pricing")
except AuthenticationError:
    print("Bad token. Get one at https://socialapis.io/auth/signup")
```

Every typed exception carries `.status_code`, `.request_id`, and
`.body` for debugging. The `request_id` is the same value our backend
logs — paste it into a support email and we can find the exact call.

## Configuration

```python
Facebook(
    api_token="...",
    base_url="https://api.socialapis.io",   # for staging / mocking
    timeout=30.0,                            # seconds; default 30
)
```

## Pricing

| Tier | Calls / month | Price |
|---|---|---|
| **Free** | 200 | $0 |
| Pro | 1,500 | $4.99 |
| Ultra | 30,000 | $49 |
| Mega | 120,000 | $179 |
| Enterprise | Custom | [Contact us](https://socialapis.io/contact-us) |

One credit per successful response. Failed calls (4xx caused by bad input)
don't consume credits.

## What's covered today (v0.1)

- [x] `Facebook.get_page_info(page)` — page metadata
- [x] Typed Pydantic models for every response
- [x] Sync + async clients
- [x] Typed exception hierarchy
- [x] `FacebookScraper` alias for kevinzg drop-in migration
- [ ] `Facebook.get_posts(page, limit=N)` — paginated posts *(v0.2)*
- [ ] `Facebook.get_group_details(group)` *(v0.2)*
- [ ] `Facebook.get_group_posts(group)` *(v0.2)*
- [ ] `Facebook.search_pages(query)`, `.search_posts(query)` *(v0.2)*
- [ ] `Facebook.search_ads(...)` — Meta Ads Library *(v0.3)*
- [ ] `Facebook.search_marketplace(...)` *(v0.3)*
- [ ] `Instagram` namespace — profiles, posts, reels, highlights *(v0.4)*

We're shipping these in small releases to keep each version reviewable.
The hosted API supports all of them today via REST — you can use the SDK
for what's covered and `httpx` directly for the rest.

## Other languages

- **JavaScript / TypeScript** — coming soon. [Notify me →](https://socialapis.io/api-sources)
- **PHP** — coming soon. [Notify me →](https://socialapis.io/api-sources)
- **Go** — coming soon. [Notify me →](https://socialapis.io/api-sources)
- Any language right now: hit the REST API directly with `curl` / `fetch` / `requests`. Docs at [docs.socialapis.io](https://docs.socialapis.io).

## Support

- Docs: [docs.socialapis.io](https://docs.socialapis.io)
- Issues: [github.com/SocialAPIsHub/socialapis-python/issues](https://github.com/SocialAPIsHub/socialapis-python/issues)
- Email: [support@socialapis.io](mailto:support@socialapis.io)
- Telegram (fastest): [t.me/socialapis](https://t.me/socialapis)

## License

MIT — see [LICENSE](LICENSE).

---

<sub>Keywords: facebook scraper python, facebook scraper alternative,
facebook api python, facebook scraper not working, kevinzg facebook scraper
fork, instagram scraper python, instagram api python, facebook graph api
alternative, facebook api without oauth, meta api python sdk,
facebook data extraction, social media api python.</sub>
