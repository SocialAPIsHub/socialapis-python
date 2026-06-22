# Contributing to socialapis

Thanks for the interest. This SDK ships the Python client for the
[socialapis.io](https://socialapis.io) REST API — most contributions are
small bug fixes, doc improvements, or new endpoint method wrappers when
the backend adds a new route.

## What kinds of contributions are welcome

- Bug fixes (anything that produces wrong / surprising output)
- New endpoint method wrappers when the API adds an endpoint
- Pydantic model improvements (correcting field names, adding missing
  fields, tightening types)
- Test coverage improvements
- Documentation: typos, clearer examples, fixing stale field references
- Performance improvements that don't change behaviour

## What's NOT a fit

- **Adding a new social platform.** The SDK can only wrap endpoints that
  exist on the backend. New platforms (TikTok / X / LinkedIn / YouTube)
  need backend work first; once they're live, we add the methods here.
- **Breaking changes to public method signatures** without a strong
  reason. We try hard to keep `from socialapis import Facebook` stable.
- **Removing the migration aliases** (`FacebookScraper`,
  `InstagramScraper`). They're part of the public contract for users
  migrating from kevinzg/arc298.

## Setup

```bash
git clone https://github.com/SocialAPIsHub/socialapis-python.git
cd socialapis-python
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Requires Python 3.10+.

## Verify your change

Run these locally before opening a PR — CI will reject anything that
fails them:

```bash
ruff check .                    # lint
ruff format --check .           # formatting
mypy socialapis tests           # type check (--strict)
pytest                          # tests + coverage gate (70% minimum)
```

`ruff check --fix .` and `ruff format .` will auto-fix most lint/format
issues.

## Optional: integration smoke test

For changes that touch the typed-model methods (`get_page_info`,
`get_profile_details`, `get_group_details`), re-run the smoke script
against a real API token to confirm Pydantic field names still match the
live API:

```bash
export SOCIALAPIS_TOKEN="<your token from https://socialapis.io/auth/signup>"
python scripts/integration_smoke.py
```

The script never prints the token. Cost: ~13 credits out of your 200/month
free tier.

## PR conventions

- **Branch off `main`** with a prefixed name: `fix/`, `feat/`, `docs/`,
  `chore/`, `refactor/`
- **Commit subject**: short imperative ("fix: …"), no trailing period
- **Squash-merge** is the merge style (keeps `main` history linear and
  readable). The squash commit's subject becomes the entry on `main`.
- **CHANGELOG.md** — update under `## [Unreleased]` for any user-visible
  change (new method, removed field, behaviour change)
- **CI must be green** before merge — lint, types, tests on Python
  3.10 / 3.11 / 3.12 / 3.13

## Reporting bugs

Open an issue with:

- Python version + SDK version (`python -c "from socialapis import __version__; print(__version__)"`)
- Minimal reproduction (~20 lines if possible)
- What you expected vs. what happened
- The `request_id` from the response if the SDK raised an `APIError`
  (it's on every typed exception — `exc.request_id`)

Security issues: please don't open a public issue. See
[`SECURITY.md`](SECURITY.md) for the disclosure flow.

## Releases

Releases are cut from `main` on a `vX.Y.Z` tag push. The release workflow
publishes to PyPI via Trusted Publishing — no manual API tokens involved.
The CHANGELOG section becomes the GitHub Release notes.
