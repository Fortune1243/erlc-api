# Changelog

## Unreleased

- Added typed response models in `erlc_api.models` and `_typed` endpoint methods across v1 and v2.
- Added `ModelDecodeError` for typed decode top-level shape mismatches.
- Added utility modules:
  - `erlc_api.utils.filters`
  - `erlc_api.utils.diff`
  - `erlc_api.utils.polling`
- Added Discord adapters in `erlc_api.discord` for player/mod-call/command-log event iteration.
- Added web adapters in `erlc_api.web` for DTO serialization and dashboard metrics aggregation.
- Expanded tests for typed decoding, utilities, polling, adapters, and additive import compatibility.
- Updated README with raw-vs-typed usage, Discord/web examples, and migration notes.
- Added GitHub Wiki source docs under `docs/wiki/` with Discord-first and web/backend onboarding pages.
- Added strength-led README competitive snapshot with full matrix and wiki links.
- Added wiki publishing scripts:
  - `scripts/publish_wiki.ps1`
  - `scripts/publish_wiki.sh`
- Added manual GitHub Actions workflow `.github/workflows/publish-wiki.yml` for wiki sync via `workflow_dispatch`.

## 1.0.1 - 2026-03-05

- Added `path_template` plumbing through client/http request flow for stable rate-limit bucket fallback and caching.
- Added per-endpoint `path_template` usage in v1/v2 wrappers.
- Hardened production hygiene:
  - `scripts/smoke.py` now reads `ERLC_SERVER_KEY` from environment and fails fast when missing.
  - Added `.gitignore` entries for local secrets, virtualenvs, and caches.
  - Added `pytest.ini` for `pytest-asyncio` configuration.
  - Added GitHub Actions CI workflow for Python 3.11/3.12.
  - Expanded README with install, quickstart, validation, error taxonomy, and multi-server behavior notes.
