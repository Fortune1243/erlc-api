# FAQ

## Is this an official PRC SDK?

No. This is an independent community wrapper for the ER:LC PRC Private Server API.

## Why choose this over a thin endpoint wrapper?

Because production workloads need reliability features: bucket-aware limiter behavior, retry controls, request coalescing, caching, and structured error handling.

## Can I use one client for multiple servers?

Yes. Use one `ERLCClient` and create per-server contexts with `client.ctx(server_key)`.

## Does it support both v1 and v2?

Yes. Both are supported with raw methods and typed methods.

## Does typed mode replace raw mode?

No. Raw mode is fully available. Typed/validated modes are additive.

## How do validated responses work?

Install `erlc-api[pydantic]` and use `client.v2.server_validated(...)`, `server_all_validated(...)`, or `server_default_validated(...)`.

## Why is `:log` blocked in `client.v1.command(...)`?

To avoid command-channel misuse for logging workflows. Use command log retrieval/parsing helpers instead.

## How do I run command syntax checks without sending?

Use `dry_run=True` with `client.v1.command(...)` / `send_command(...)`.

## How do I monitor live server state?

Use `async with client.track_server(ctx) as tracker:` and register callbacks (`player_join`, `player_leave`, `staff_join`, `staff_leave`, `command_executed`, `snapshot`).

## How do I inspect cache/replay state?

- `client.cache_stats()`
- `await client.invalidate(ctx, endpoint=None)`
- `client.request_replay(limit=...)`

## How do I publish this wiki?

Use `scripts/publish_wiki.ps1` (PowerShell) or `scripts/publish_wiki.sh` (bash) to sync `docs/wiki/` into the GitHub wiki repo.
