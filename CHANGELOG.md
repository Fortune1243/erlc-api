# Changelog

Format follows the spirit of [Keep a Changelog](https://keepachangelog.com/).

## [3.1.0] - 2026-05-11

### Added

- Added lazy `erlc_api.roblox` with `RobloxClient`, `AsyncRobloxClient`, `RobloxUser`, TTL caching, raw payload access, username lookup, batch user lookup, and module-local Roblox errors.
- Added a `roblox` install extra for explicit Roblox lookup installs without adding a new base dependency.
- Added Roblox utility docs, README discoverability, navigation links, and focused tests for sync, async, cache, raw, missing-user, rate-limit, API-error, and network-error behavior.
- Added GitHub issue templates, a pull request template, and Dependabot configuration for repository maintenance.

### Changed

- Expanded README project links, utility examples, reliability guidance, support text, and license/disclaimer notes.
- Refined repository guidance in `AGENTS.md` for the v3 public API shape, lazy utility modules, release checks, documentation, and security expectations.

## [3.0.0] - 2026-05-10

### Added

- Added `Client` and `AsyncClient` aliases for the existing sync and async clients.
- Added `from_env(...)` constructors using `ERLC_SERVER_KEY` and optional `ERLC_GLOBAL_KEY`.
- Added client-level `bundle(...)`, `logs(...)`, and `preview_command(...)` helpers for simpler common reads and command previews.
- Added `policy=` support to `command(...)` so command policy validation can happen directly in the execution call.
- Added `CommandPreview` and `ServerLogs` typed dataclasses.
- Added list-like `StaffList` behavior, role-specific staff member helpers, `ServerBundle.included_sections`, `ServerBundle.has_section(...)`, and safe list properties such as `players_list`.
- Added runnable examples under `examples/`.
- Added a concise migration guide for v3.

### Changed

- Refocused README as a short introduction and moved detailed reference content into `docs/wiki`.
- Reordered wiki navigation around reference-first docs, followed by examples and migration material.
- Bumped package version metadata to `3.0.0`.

## [2.4.0] - 2026-05-04

### Added

- Added `PermissionLevel` with ordered permission comparisons via `player.permission_level` and `staff_member.permission_level`.
- Added lazy `erlc_api.vehicles` with vehicle catalog parsing, `VehicleTools`, `PlayerVehicleBundle`, and vehicle model/year/plate/owner helpers, with catalog ergonomics inspired by TychoTeam/prc.api-py's MIT-licensed vehicle typing work.
- Added lazy `erlc_api.emergency` with `EmergencyCallTools` for active, unresponded, team, nearest-call, and summary workflows.
- Added wanted-star filters, finders, and watcher events for new, cleared, escalated, decreased, and general wanted changes.
- Added `CommandResult.command_id` parsing for `commandId` style PRC responses.
- Added command metadata for display names, categories, target hints, and recommended minimum permission levels.
- Added `CONTRIBUTING.md`, `SECURITY.md`, `comparison.md`, and new docs pages for scaling, vehicles, emergency calls, permission levels, and wanted stars.

### Changed

- Improved dynamic rate-limiter safety with per-bucket/per-scope request queue locks.
- Updated README and docs to highlight Python `>=3.11`, multi-server usage, custom-command webhooks, explicit caching, and v2.4.0 feature helpers.

### Fixed

- Renamed the misspelled root comparison file to `comparison.md`.

## [2.3.1] - 2026-05-04

### Added

- Made dynamic client rate limiting default-on for `AsyncERLC` and `ERLC`.
- Kept `rate_limited=False` as an explicit opt-out for applications with their own limiter.
- Standardized user-facing package naming around `erlc-api.py`.
- Added top-level `__version__`.
- Added `CommandPolicy`, `CommandPolicyResult`, and `CommandPolicyError` for allowlist-first command guardrails.
- Added lazy `erlc_api.security.key_fingerprint(...)` for safe key diagnostics.
- Clarified `raw=True` behavior for full endpoint payloads versus section helper payloads.
- Reworked Discord and web command examples around lifecycle, permissions/auth, cooldowns, policy validation, and dry-run previews.
- Added known limitations and endpoint/support matrix documentation.
- Added a regression test that documented extras resolve to `pyproject.toml` optional dependencies.

## [2.3.0] - 2026-05-04

- Added lazy workflow utility modules: `location`, `bundle`, `rules`, `multiserver`, `discord_tools`, `diagnostics`, `cache`, `status`, and `command_flows`.
- Added bundle presets, typed status summaries, dependency-free Discord payload builders, memory TTL caching, command-flow previews, and multi-server read aggregation.
- Added optional Pillow-backed map rendering behind `erlc-api.py[location]`.
- Fixed dynamic rate-limiter retry-after windows so observed cooldowns expire correctly.
- Kept workflow utilities outside top-level `erlc_api` imports and avoided new base dependencies.

## [2.2.0] - 2026-05-03

- Added opt-in dynamic client rate limiting with `rate_limited=True`.
- Added lazy `ratelimit` utilities for response-header-driven limiter state.
- Added lazy `error_codes` utilities for explaining PRC error codes and exception mappings.
- Reused the public error-code table for internal transport exception mapping.

## [2.1.0] - 2026-05-03

- Added ops utility modules: `snapshot`, `audit`, `idempotency`, and `limits`.
- Added JSONL snapshot persistence, JSON-safe audit events, TTL dedupe helpers, and conservative polling guidance.
- Added `custom_commands` as a framework-neutral router for PRC Event Webhook messages that start with `;`.
- Kept new utilities lazy, stdlib-only, and outside top-level `erlc_api` exports.

## [2.0.0] - 2026-05-03

Breaking lightweight release.

- Replaced the grouped public API with flat `AsyncERLC` and `ERLC` clients.
- Added typed dataclass returns by default plus `raw=True` for exact API payloads.
- Made v2 the default for server data and command execution.
- Kept v1 only for endpoints not covered by v2, such as bans.
- Added flexible command creation through plain strings and `cmd`.
- Added optional global API key support via the `Authorization` header.
- Removed public context objects, v1/v2 groups, pydantic validation models, Redis/cache support, metrics, request replay, tracing, circuit breaker, and request coalescing.
- Kept pure utilities, web/Discord helpers, and event webhook support.
- Kept base dependencies minimal and moved feature dependencies into extras.
- Added explicit lazy utility modules: `find`, `filter`, `sort`, `group`, `diff`, `wait`, `watch`, `format`, `analytics`, `export`, `moderation`, `time`, and `schema`.
- Added utility extras: `export`, `time`, `rich`, `scheduling`, `utils`, and `all`.

## [1.0.1] - 2026-03-05

- Last release of the original grouped async API.
