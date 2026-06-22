# socialapis — Python SDK for Facebook + Instagram public data

[![PyPI](https://img.shields.io/pypi/v/socialapis-sdk?cacheSeconds=300&label=PyPI&logo=pypi&logoColor=white)](https://pypi.org/project/socialapis-sdk/)
[![Python versions](https://img.shields.io/pypi/pyversions/socialapis-sdk)](https://pypi.org/project/socialapis-sdk/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

The modern alternative to [`kevinzg/facebook-scraper`](https://github.com/kevinzg/facebook-scraper)
and [`arc298/instagram-scraper`](https://github.com/arc298/instagram-scraper) —
real-time Facebook + Instagram data via REST, **no OAuth dance, no app
review, no scraper maintenance**. Powered by hosted infrastructure at
[socialapis.io](https://socialapis.io).

```bash
pip install socialapis-sdk
```

```python
from socialapis import Facebook, Instagram

fb = Facebook(api_token="...")
page = fb.get_page_info("EngenSA")
print(page.title, page.followers_count, page.category)

ig = Instagram(api_token="...")
profile = ig.get_profile_details("instagram")
print(profile.username, profile.followers_count)
```

**[Get a free API token →](https://socialapis.io/auth/signup)** — 200 calls/month, no credit card

## One-line migration

If your code currently uses [`kevinzg/facebook-scraper`](https://github.com/kevinzg/facebook-scraper)
or [`arc298/instagram-scraper`](https://github.com/arc298/instagram-scraper), the migration is
**literally one import line**:

```python
# Before — kevinzg/facebook-scraper (abandoned since 2022)
from facebook_scraper import get_page_info, get_posts

# After — socialapis (alias preserves the name)
from socialapis import FacebookScraper
fb = FacebookScraper(api_token="...")
fb.get_page_info("EngenSA")
fb.get_page_posts("EngenSA")

# Same for Instagram
from socialapis import InstagramScraper
ig = InstagramScraper(api_token="...")
```

`FacebookScraper` and `InstagramScraper` are exact aliases of `Facebook` and `Instagram` —
identical behavior, identical type signatures. They exist purely to keep the import
line greppable during migration.

---

## Why this exists

`kevinzg/facebook-scraper` has 9.5k+ GitHub stars and was the default Python library for
scraping Facebook for years. It's been **abandoned since 2022**. `arc298/instagram-scraper`
(8.5k stars) is in similar shape. Every Meta DOM change breaks them; fixes pile up in
unmerged PRs; downloads drift to forks that fix one bug and break two.

This SDK is the **drop-in successor**:

| | `kevinzg/facebook-scraper` (2018-era) | `socialapis` (2026) |
|---|---|---|
| **Maintenance** | Abandoned 2022 | Active; we run prod for 7M+ calls/mo |
| **Reliability** | Breaks on every Meta HTML change | Hosted backend; we absorb breakage |
| **Type hints** | None | Strict throughout |
| **Async support** | No | `Facebook` + `AsyncFacebook` classes |
| **HTTP client** | `requests` | `httpx` |
| **Validation** | Manual dict parsing | Pydantic v2 models |
| **Auth** | None (scrapes anonymously) | Single `x-api-token` header |
| **Pagination** | Generator with edge-case bugs | Cursor-based; API decides page size |
| **Error handling** | Generic exceptions | Typed hierarchy (`RateLimitError`, etc.) |
| **CI / tests** | Manual against live FB | Recorded HTTP fixtures, Python 3.10–3.13 |
| **Coverage** | Page posts, group posts only | **45+ endpoints** across FB + IG |

The trade-off: instead of running a scraper yourself, you make a REST call to our hosted
API. **200 calls/month free**, no credit card. Paid plans start at $4.99/mo for 1,500
calls.

## What's covered (v0.1)

### Facebook (`Facebook` / `AsyncFacebook`)

**Pages**
- `get_page_id(page)` — resolve a URL/slug to numeric ID
- `get_page_info(page)` → `PageInfo` — page metadata (typed model)
- `get_page_posts(page)` — recent posts
- `get_page_reels(page)` — short-form videos
- `get_page_videos(page)` — long-form videos

**Groups**
- `get_group_id(group)`
- `get_group_details(group)` → `GroupInfo` (typed model)
- `get_group_metadata(group)` — lightweight metadata only
- `get_group_posts(group)`
- `get_group_videos(group_id)`

**Posts**
- `get_post_id(post)` — extract numeric ID from URL
- `get_post_details(post)` — reactions, media, author
- `get_post_details_extended(post)` — + views, video URLs, author verification
- `get_post_comments(post)` — pass `include_reply_info="true"` for reply cursors
- `get_comment_replies(comment_feedback_id, expansion_token)`
- `get_post_attachments(post_id)`
- `get_video_post_details(video_id)`

**Search**
- `search_pages(query)` — supports `location_id` for geo-filtering
- `search_people(query)`
- `search_locations(query)` — returns location IDs for use in other endpoints
- `search_posts(query)` — supports recency + location filters
- `search_videos(query)`

**Meta Ads Library**
- `get_ads_countries()` — supported countries
- `search_ads(query)` — by keyword + country + activeStatus
- `get_ads_page_details(page_id)`
- `get_ad_archive_details(ad_archive_id, page_id)`
- `search_ads_by_keywords(query)`

**Marketplace**
- `search_marketplace(query)` — supports lat/lng, price, condition filters
- `get_listing_details(listing_id)`
- `get_seller_details(seller_id)`
- `get_marketplace_categories()`
- `get_city_coordinates(city)` — for lat/lng filtering
- `search_vehicles()` — bedrooms-style filters; lat/lng required
- `search_rentals()`

**Media**
- `download_media(url)` — resolve to direct downloadable URL

### Instagram (`Instagram` / `AsyncInstagram`)

**Profiles**
- `get_user_id(profile)` — username/URL → numeric user_id
- `get_profile_details(username)` → `ProfileInfo` (typed model)
- `get_profile_posts(username)`
- `get_profile_reels(user_id)`
- `get_profile_highlights(user_id)`
- `get_highlight_details(highlight_id)`

**Posts**
- `get_post_id(post)` — extract shortcode from any post URL
- `get_post_details(shortcode)`

**Reels**
- `get_reels_feed()` — trending feed
- `get_reels_by_audio(audio_id)` — all reels using a specific track

**Search + Locations**
- `search(keyword)` — popular results (users / hashtags / places)
- `get_location_posts(location_id)` — top or recent
- `get_nearby_locations(location_id)`

### Account (`Account` / `AsyncAccount`)

Free calls — don't consume credits.

- `get_usage()` — credit balance, plan, billing period
- `get_top_ups()` — auto top-up settings + history
- `get_limits()` — rate limit, concurrent-task cap, allowed packages

## Pagination — no `limit=N`, just cursors

Every endpoint that returns a list lets the API decide page size. To paginate, take the
cursor from the response body and pass it back as a kwarg on the next call:

```python
fb = Facebook(api_token="...")

# First page
result = fb.get_page_posts("EngenSA")
posts = result["posts"]
cursor = result.get("next_cursor")  # actual key varies by endpoint — check docs

# Next page
while cursor:
    result = fb.get_page_posts("EngenSA", cursor=cursor)
    posts.extend(result["posts"])
    cursor = result.get("next_cursor")
```

We deliberately don't impose a uniform `limit=N` parameter — it would drift from the
API's actual semantics. The API's response always tells you whether there's more.

## Forward-compat via `**kwargs`

Every method accepts arbitrary kwargs and forwards them as query params. If the API adds
a new filter tomorrow, you can use it today — no SDK release required:

```python
fb.search_ads("fitness", country="US", activeStatus="Active", some_new_filter="x")
# Sends: ?query=fitness&country=US&activeStatus=Active&some_new_filter=x
```

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

Every typed exception carries `.status_code`, `.request_id`, and `.body` for debugging.
The `request_id` is the same value our backend logs — paste it into a support email
and we can find the exact call.

## Async

Same method surface; methods are coroutines.

```python
import asyncio
from socialapis import AsyncFacebook

async def main():
    async with AsyncFacebook(api_token="...") as fb:
        pages = await asyncio.gather(*[
            fb.get_page_info(slug)
            for slug in ["EngenSA", "Microsoft", "GitHub"]
        ])
        for page in pages:
            print(page.title, page.followers_count)

asyncio.run(main())
```

## Pricing

| Tier | Calls / month | Price |
|---|---|---|
| **Free** | 200 | $0 |
| Pro | 1,500 | $4.99 |
| Ultra | 30,000 | $49 |
| Mega | 120,000 | $179 |
| Enterprise | Custom | [Contact us](https://socialapis.io/contact-us) |

One credit per successful response. Failed calls (4xx caused by bad input) don't
consume credits.

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
