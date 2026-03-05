# Changelog

## 1.0.1 - 2026-03-05

- Added `path_template` plumbing through client/http request flow for stable rate-limit bucket fallback and caching.
- Added per-endpoint `path_template` usage in v1/v2 wrappers.
- Hardened production hygiene:
  - `scripts/smoke.py` now reads `ERLC_SERVER_KEY` from environment and fails fast when missing.
  - Added `.gitignore` entries for local secrets, virtualenvs, and caches.
  - Added `pytest.ini` for `pytest-asyncio` configuration.
  - Added GitHub Actions CI workflow for Python 3.11/3.12.
  - Expanded README with install, quickstart, validation, error taxonomy, and multi-server behavior notes.
