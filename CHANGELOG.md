# Changelog

## 2.1.0 - 2026-05-03

- Added ops utility modules: `snapshot`, `audit`, `idempotency`, and `limits`.
- Added JSONL snapshot persistence, JSON-safe audit events, TTL dedupe helpers, and conservative polling guidance.
- Added `custom_commands` as a framework-neutral router for PRC Event Webhook messages that start with `;`.
- Kept new utilities lazy, stdlib-only, and outside top-level `erlc_api` exports.

## 2.0.0 - 2026-05-03

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

## 1.0.1 - 2026-03-05

- Last release of the original grouped async API.
