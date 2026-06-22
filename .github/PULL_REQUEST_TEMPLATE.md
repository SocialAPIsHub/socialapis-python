## Summary

<!--
What does this PR do, and why? 2-3 sentences is usually enough.
-->

## Test plan

<!--
Bulleted checklist of what you ran locally to verify the change.
At minimum, all four of these should pass:
-->

- [ ] `ruff check .`
- [ ] `ruff format --check .`
- [ ] `mypy socialapis tests`
- [ ] `pytest`

For changes touching `get_page_info`, `get_profile_details`, or
`get_group_details`, also re-run the smoke test:

- [ ] `python scripts/integration_smoke.py`  (requires `SOCIALAPIS_TOKEN`)

## Checklist

- [ ] `CHANGELOG.md` updated under `## [Unreleased]` for any user-visible change
- [ ] Public method signatures unchanged (or a clear reason if changed)
- [ ] If a Pydantic model field was added/removed, real-API behaviour verified
