# Single source of truth for the package version.
#
# Bumped by the release workflow (.github/workflows/release.yml). NEVER edit
# this manually for a release — use `git tag vX.Y.Z` and the CI does the
# rest via hatchling's dynamic-version feature (see pyproject.toml).

__version__ = "0.1.1"
