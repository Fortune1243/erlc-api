# Changelog

## Unreleased

- Added advanced transport resilience:
  - configurable retry policy (`retry_429`, `retry_5xx`, `retry_network`)
  - exponential backoff + jitter controls
  - request coalescing for duplicate in-flight idempotent GET calls
  - reset-aware rate-limit pre-acquire behavior
  - optional per-bucket circuit breaker
- Added cache layer:
  - in-memory TTL cache for idempotent GET endpoints
  - optional Redis backend (`erlc-api[redis]`)
  - cache controls: `ERLCClient.invalidate(...)`, `clear_cache()`, `cache_stats()`
- Expanded v2 modeling:
  - `PlayerLocation`, `VehicleColor`, `EmergencyCall`
  - support for `Helpers`, `EmergencyCalls`, `WantedStars`, vehicle color metadata
- Added optional validated v2 decoding (`erlc-api[pydantic]`):
  - `server_validated`, `server_all_validated`, `server_default_validated`
- Added command ergonomics:
  - `CommandBuilder`, command syntax validation, dry-run support
  - `command_with_tracking` + command history
  - log stream helpers (`command_logs_stream`, `join_logs_stream`, `kill_logs_stream`)
  - command metric emission to configured `metrics_sink.on_command(...)`
- Added live state tracker:
  - `client.track_server(ctx)` with callback events for joins/leaves/commands/snapshots
  - typed tracker event enum `TrackerEvent` with backward-compatible string event support
- Expanded error taxonomy:
  - `PermissionDeniedError`, `PlayerNotFoundError`, `ServerEmptyError`, `RobloxCommunicationError`, `InvalidCommandError`, `CircuitOpenError`
- Added observability/config integration points:
  - metrics sink support in client config
  - optional `structlog` and OpenTelemetry tracing switches
  - redacted request replay buffer (`request_replay`)
- Added packaging improvements:
  - `py.typed` marker
  - extras: `pydantic`, `redis`, `observability`, `all`
- Updated README/wiki documentation to match implemented APIs and behavior.

## 1.0.1 - 2026-03-05

- Added `path_template` plumbing through client/http request flow for stable rate-limit bucket fallback and caching.
- Added per-endpoint `path_template` usage in v1/v2 wrappers.
- Hardened production hygiene:
  - `scripts/smoke.py` now reads `ERLC_SERVER_KEY` from environment and fails fast when missing.
  - Added `.gitignore` entries for local secrets, virtualenvs, and caches.
  - Added `pytest.ini` for `pytest-asyncio` configuration.
  - Added GitHub Actions CI workflow for Python 3.11/3.12.
  - Expanded README with install, quickstart, validation, error taxonomy, and multi-server behavior notes.
