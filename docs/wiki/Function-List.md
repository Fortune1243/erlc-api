# Function List (Beginner-Friendly)

Use this page as a quick index of what to call first when building ER:LC apps with `erlc-api`.

## 1. Client lifecycle

- `ERLCClient()` - create one shared API client.
- `await client.start()` / `await client.close()` - manual lifecycle control.
- `async with ERLCClient() as client:` - recommended lifecycle pattern.
- `client.ctx(server_key)` - build a server context for a specific key.
- `await client.validate_key(ctx)` / `await client.health_check(ctx)` - key validation helper.

## 2. v1 endpoint methods

Raw:

- `client.v1.server(ctx)`
- `client.v1.players(ctx)`
- `client.v1.join_logs(ctx)`
- `client.v1.queue(ctx)`
- `client.v1.kill_logs(ctx)`
- `client.v1.command_logs(ctx)`
- `client.v1.mod_calls(ctx)`
- `client.v1.bans(ctx)`
- `client.v1.vehicles(ctx)`
- `client.v1.staff(ctx)`
- `client.v1.command(ctx, command, dry_run=False)`

Typed:

- `client.v1.server_typed(ctx)`
- `client.v1.players_typed(ctx)`
- `client.v1.join_logs_typed(ctx)`
- `client.v1.queue_typed(ctx)`
- `client.v1.kill_logs_typed(ctx)`
- `client.v1.command_logs_typed(ctx)`
- `client.v1.mod_calls_typed(ctx)`
- `client.v1.bans_typed(ctx)`
- `client.v1.vehicles_typed(ctx)`
- `client.v1.staff_typed(ctx)`
- `client.v1.command_typed(ctx, command, dry_run=False)`

Command helpers:

- `client.v1.send_command(...)`
- `client.v1.command_with_tracking(...)`
- `client.v1.command_history(...)`
- `CommandBuilder.pm(...)`, `CommandBuilder.rank(...)`, `CommandBuilder.warn(...)`, `CommandBuilder.ban(...)`

## 3. v2 endpoint methods

Raw:

- `client.v2.server(...)`
- `client.v2.server_default(ctx)`
- `client.v2.server_all(ctx)`

Typed dataclass:

- `client.v2.server_typed(...)`
- `client.v2.server_default_typed(ctx)`
- `client.v2.server_all_typed(ctx)`

Validated (`pydantic` extra required):

- `client.v2.server_validated(..., strict=False)`
- `client.v2.server_default_validated(ctx, strict=False)`
- `client.v2.server_all_validated(ctx, strict=False)`

Fluent builder:

- `client.v2.server_query(ctx)` then `.include_*()` then `.fetch()` / `.fetch_typed()` / `.fetch_validated()`

## 4. Tracking, streaming, and reliability helpers

- `client.track_server(ctx, interval_s=...)` - live state tracker.
- `TrackerEvent` - typed event enum for tracker callbacks.
- `client.v1.command_logs_stream(...)`
- `client.v1.join_logs_stream(...)`
- `client.v1.kill_logs_stream(...)`
- `await client.invalidate(ctx, endpoint=None)`
- `await client.clear_cache()`
- `client.cache_stats()`
- `client.request_replay(limit=...)`

## 5. Event webhook helpers (custom `;` commands + emergency calls)

- `extract_webhook_signature_headers(headers)`
- `verify_event_webhook_signature(...)`
- `assert_valid_event_webhook_signature(...)`
- `decode_event_webhook_payload(payload, command_prefix=";")`
- `parse_custom_command_text(text, prefix=";")`
- `EventWebhookRouter(...)`
- `WebhookEventType` (`CUSTOM_COMMAND`, `EMERGENCY_CALL`, `UNKNOWN`)

For setup steps, see [Event-Webhooks-and-Custom-Commands.md](./Event-Webhooks-and-Custom-Commands.md).
