# Changelog

## Unreleased

- Added advanced transport resilience:
  - configurable retry policy (`retry_429`, `retry_5xx`, `retry_network`, jitter)
  - request coalescing for duplicate in-flight idempotent GET calls
  - reset-aware bucket pre-acquire and per-bucket circuit breaker behavior
- Added cache layer:
  - in-memory TTL cache for idempotent GET endpoints
  - optional Redis backend (`erlc-api[redis]`)
  - `ERLCClient.invalidate(...)`, cache stats, and cache clear APIs
- Added richer v2 typed modeling:
  - `PlayerLocation`, `VehicleColor`, `EmergencyCall`
  - `helpers`, `emergency_calls`, `wanted_stars`, and vehicle color fields in typed bundle parsing
- Added optional validated v2 decoding via Pydantic v2 (`erlc-api[pydantic]`)
  - `server_validated`, `server_all_validated`, `server_default_validated`
- Added command ergonomics:
  - `CommandBuilder`, syntax validation, dry-run support
  - command history, `command_with_tracking`, and log correlation with timeout
  - async log streaming helpers on v1 (`command_logs_stream`, `join_logs_stream`, `kill_logs_stream`)
- Added live server state tracker (`client.track_server(ctx)`) with event callbacks for join/leave and command events.
- Added observability hooks:
  - metrics sink integration points
  - optional `structlog` and OpenTelemetry tracing integration switches
  - redacted request replay buffer for debugging
- Added packaging/type improvements:
  - `py.typed` marker
  - new extras: `pydantic`, `redis`, `observability`, `all`
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
