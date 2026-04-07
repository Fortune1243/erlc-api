# erlc-api

A modern, advanced asynchronous Python wrapper for the **ER:LC PRC Private Server API** with support for **v1** and **v2** endpoints, multi-server contexts, resilient rate-limit handling, and production-oriented error management.

> **Release status:** this repository is currently at **v1.0.1**.
>
> `erlc-api` is built for bot developers, dashboards, panels, automations, and backend services that need reliable access to ER:LC server data and commands.

---

## Why `erlc-api`

`erlc-api` is designed for developers who do not want a thin wrapper that simply forwards requests. It provides a structured async client, isolates rate limits per server key and bucket, avoids leaking full server keys in logs, and exposes a clean error model for production use.

### Core capabilities

- **Async-first architecture** built on `httpx`
- **ER:LC API v1 and v2 support**
- **Multi-server workflow** through per-server contexts created from one client
- **Bucket-aware rate-limit handling** using API headers
- **Automatic retry handling** for safe/idempotent requests and `429` responses
- **No automatic replay of non-idempotent command calls**
- **Safe key fingerprinting** for logs and internal routing
- **Structured validation flow** for checking server keys during setup
- **Clear exception taxonomy** for auth, rate-limit, not-found, API, and network failures
- **Remote command execution** through the PRC command endpoint

---

## Supported API coverage

### v1 endpoints

The wrapper exposes the following v1 methods:

| Method | Purpose |
|---|---|
| `client.v1.command(ctx, command)` | Run a remote ER:LC command except `:log` |
| `client.v1.server(ctx)` | Get server status/details |
| `client.v1.players(ctx)` | Get current players |
| `client.v1.join_logs(ctx)` | Get join logs |
| `client.v1.queue(ctx)` | Get queue data |
| `client.v1.kill_logs(ctx)` | Get kill logs |
| `client.v1.command_logs(ctx)` | Get command logs |
| `client.v1.mod_calls(ctx)` | Get moderator calls |
| `client.v1.bans(ctx)` | Get bans |
| `client.v1.vehicles(ctx)` | Get current vehicles |
| `client.v1.staff(ctx)` | Get staff list |

`client.v1.command(...)` intentionally rejects the `:log` command with `ValueError`. If your application needs a `:log`-driven workflow, implement that behavior outside this wrapper.

### v2 endpoints

The wrapper exposes the following v2 methods:

| Method | Purpose |
|---|---|
| `client.v2.server(ctx, ...)` | Fetch `/v2/server` with granular include flags |
| `client.v2.server_all(ctx)` | Fetch all supported v2 datasets in one request |
| `client.v2.server_default(ctx)` | Fetch a practical default subset (`players`, `queue`, `staff`) |

PRC controls access to API v2. The wrapper exposes the v2 client surface, but your server key must have PRC-granted v2 access for these requests to succeed.

### v2 include flags supported

`client.v2.server(...)` supports these flags:

- `players`
- `staff`
- `join_logs`
- `queue`
- `kill_logs`
- `command_logs`
- `mod_calls`
- `vehicles`

When `players=True`, player location data is returned exactly as provided by PRC in `Players[].Location`. That includes fields such as `LocationX`, `LocationZ`, `PostalCode`, `StreetName`, and `BuildingNumber`. This wrapper currently passes that payload through as raw JSON and does not add a dedicated typed location model.

---

## Public helper objects and utilities

### Main client

| Object / method | Purpose |
|---|---|
| `ERLCClient()` | Main async client |
| `await client.start()` | Start the HTTP client |
| `await client.close()` | Close the HTTP client |
| `client.ctx(server_key)` | Create a per-server `ERLCContext` |
| `await client.validate_key(ctx)` | Validate a server key without forcing setup flows to rely on exceptions |

### Context and utilities

| Object / function | Purpose |
|---|---|
| `ERLCContext` | Carries a server key safely through requests |
| `fingerprint_key(server_key)` | Returns a short printable fingerprint suitable for logs |
| `helpers.validate_server_key(client, ctx)` | Backward-compatible helper for key validation |
| `helpers.extract_log_commands(entries, ...)` | Parse fetched command log entries for `:log <payload>` commands |
| `helpers.fetch_log_commands(client, ctx, ...)` | Fetch raw command logs once, then parse matching `:log <payload>` entries |

### Validation model

`validate_key()` returns a `ValidationResult` with these statuses:

- `ok`
- `auth_error`
- `rate_limited`
- `network_error`
- `api_error`

### `:log` helpers

`client.v1.command(...)` still rejects sending `:log`, but raw command log access remains available through `client.v1.command_logs(ctx)`.

If you want convenience parsing on top of fetched command logs, this package also provides optional stateless helpers:

```python
from erlc_api.helpers import fetch_log_commands

entries = await fetch_log_commands(client, ctx, payload_prefix="incident")
```

These helpers:

- parse `:log <payload>` entries from already-fetched command logs
- optionally filter by `payload_prefix`

These helpers do not:

- poll in the background
- deduplicate entries across calls
- store cursors or state
- trigger workflows automatically

### Exception taxonomy

| Exception | Meaning |
|---|---|
| `ERLCError` | Base exception |
| `APIError` | Generic non-success API response |
| `AuthError` | Authentication/authorization failure |
| `RateLimitError` | Rate-limit response, with retry metadata when available |
| `NotFoundError` | Resource not found |
| `NetworkError` | Transport-level failure |

---

## Installation

### Editable install

```bash
pip install -e .
```

### Development install

```bash
pip install -e .[dev]
```

### Direct install from GitHub

```bash
pip install git+https://github.com/Fortune1243/erlc-api.git
```

### Requirements

- **Python 3.11+**
- `httpx>=0.27.0`

---

## Quickstart

```python
import asyncio
from erlc_api import ERLCClient


async def main() -> None:
    client = ERLCClient()
    await client.start()

    try:
        ctx = client.ctx("your-server-key")

        server_info = await client.v1.server(ctx)
        default_v2 = await client.v2.server_default(ctx)
        validation = await client.validate_key(ctx)

        print(server_info)
        print(default_v2)
        print(validation.status)
    finally:
        await client.close()


asyncio.run(main())
```

---

## Multi-server model

`erlc-api` is built so a single client can serve multiple ER:LC server keys cleanly.

```python
ctx_a = client.ctx("server-key-a")
ctx_b = client.ctx("server-key-b")
```

This enables:

- one bot serving multiple communities
- isolated rate limiting per server key and bucket
- cleaner guild-to-server-key mapping in Discord bots
- safer production logging through key fingerprints instead of raw keys

---

## Reliability and production behavior

`erlc-api` is built with production use in mind:

- reads and tracks rate-limit bucket data from response headers
- retries safe requests on transient failures
- retries `429` responses with retry hints where available
- avoids automatically replaying command requests that should not be duplicated
- keeps request routing stable with endpoint templates
- emits safer diagnostics without dumping full secrets into logs

---

## Smoke testing

Set your key and run the smoke script:

```bash
export ERLC_SERVER_KEY="your-server-key"
python scripts/smoke.py
```

PowerShell:

```powershell
$env:ERLC_SERVER_KEY="your-server-key"
python scripts/smoke.py
```

---

## Attribution and license

This repository is published under a **custom attribution license** included in `LICENSE`.

### Important credit requirement

If you use this wrapper in a public bot, panel, dashboard, service, fork, package, or other distributed project, you **must** give visible credit to the original author.

Minimum acceptable credit:

> Powered by `erlc-api` by **Avi Sehrawat** (`avi1243` on Discord)

Recommended places for attribution include:

- your repository README
- documentation or credits page
- bot `/credits` command or equivalent
- dashboard footer or about page
- package/project metadata where applicable

---

## Contact

For questions, attribution issues, collaboration, or usage inquiries:

- **Discord username:** `avi1243`
- **Discord ID:** `876471383381655562`

---

## Disclaimer

This project is an independent community wrapper for the ER:LC PRC Private Server API. It is not an official PRC product.
