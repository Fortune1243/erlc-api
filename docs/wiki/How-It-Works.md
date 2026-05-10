# How It Works

`erlc-api.py` is a thin layer over the ER:LC PRC REST API. Its job is to
attach your server key to each request, decode the JSON response into typed
Python objects, and surface PRC errors as Python exceptions you can catch and
handle — so you never have to parse raw HTTP yourself.

## The Request Flow

When you call `client.players()`, here is what happens:

1. The client attaches your `server_key` as the `Server-Key` request header.
2. `httpx` sends `GET https://api.erlc.gg/v2/server?Players=true`.
3. If PRC returns a non-200 status, the transport raises a typed exception
   (`AuthError`, `RateLimitError`, etc.) before any decoding happens.
4. On success, the JSON body is decoded into a `list[Player]` dataclass list.
5. Your code receives typed objects or a Python exception — never raw HTTP.

```python
from erlc_api import Client

with Client.from_env() as client:   # reads ERLC_SERVER_KEY from environment
    players = client.players()      # GET /v2/server?Players=true
    # players is list[Player]
    print(players[0].name)          # .name, .user_id, .team are typed fields
```

## Server Keys

A server key is a private key created in the ER:LC game settings panel. It
grants API access to your Roblox private server's data. Never share it, log it,
or commit it to source control. One key corresponds to one private server.

```python
# One default key set on the client
client = Client.from_env()  # reads ERLC_SERVER_KEY

# Override per-call for multi-server use
data_a = client.players(server_key="key-for-server-a")
data_b = client.players(server_key="key-for-server-b")
```

Use `erlc_api.security.key_fingerprint(key)` when you need to log or display a
key reference without exposing its value.

## Typed Responses

By default every endpoint returns a Python dataclass or a list of dataclasses.
Fields use Python naming conventions (`user_id`, not `UserId`). Each model
exposes:

- `.raw` — the original PRC JSON dict
- `.extra` — any fields PRC sent that the wrapper did not recognize
- `.to_dict()` — a serializable Python dict of the model's fields

Pass `raw=True` on any endpoint call when you need the exact PRC JSON instead
of a typed model.

| Method | Return type | Key fields |
| --- | --- | --- |
| `players()` | `list[Player]` | `.name`, `.user_id`, `.team`, `.permission_level` |
| `staff()` | `StaffList` | `.members`, `.admin_members`, `.mod_members` |
| `bundle()` | `ServerBundle` | `.players_list`, `.staff_members`, `.queue_list` |
| `vehicles()` | `list[Vehicle]` | `.name`, `.owner_name`, `.normalized_plate` |
| `command()` | `CommandResult` | `.success`, `.message`, `.command_id` |

## Sync vs Async

Use `Client` / `ERLC` for scripts, cron jobs, CLI tools, and Celery workers —
any code that runs top-to-bottom without an event loop.

Use `AsyncClient` / `AsyncERLC` for Discord bots, FastAPI apps, and anything
that already runs inside an `asyncio` event loop. Both clients expose identical
method names; the only difference is whether you `await` the call.

=== "Async"

    ```python
    from erlc_api import AsyncClient

    async with AsyncClient.from_env() as client:
        server = await client.server()
        print(server.name)
    ```

=== "Sync"

    ```python
    from erlc_api import Client

    with Client.from_env() as client:
        server = client.server()
        print(server.name)
    ```

**Never call the sync client from inside an async function.** `Client` calls
`httpx.Client.send()`, which blocks the thread. Inside a `discord.py` command
handler or a FastAPI route, that means blocking the entire event loop.

**Never call `asyncio.run()` inside an already-running event loop.** In a
Discord bot or FastAPI app, use `await` with `AsyncClient`.

## Rate Limits

PRC enforces per-server and per-key rate limits. The wrapper handles this in
two ways:

1. **Dynamic pre-request limiting** (`rate_limited=True`, on by default) reads
   `X-RateLimit-*` headers from successful responses and waits before a request
   when the observed bucket has no remaining capacity.
2. **Single safe retry** (`retry_429=True`, on by default) — if a `429` still
   arrives, the wrapper sleeps once using the `Retry-After` value and retries
   once. If the retry is also rate-limited, `RateLimitError` is raised.

```python
from erlc_api import AsyncClient, RateLimitError

async with AsyncClient.from_env() as client:
    try:
        players = await client.players()
    except RateLimitError as exc:
        print(f"Rate limited. Retry after {exc.retry_after_s}s")
```

For dashboards and bots that repeat the same reads, use `CachedClient` or
`AsyncCachedClient` with a TTL to reduce how often you hit the API.

## Error Handling

All exceptions inherit from `ERLCError`, so you can catch them all with one
`except` clause. Catch the most specific exception first when you need to react
differently — for example, slow down on `RateLimitError` and surface a setup
message on `AuthError`.

```python
from erlc_api import AuthError, ERLCError, RateLimitError
import asyncio

try:
    players = await client.players()
except RateLimitError as exc:
    await asyncio.sleep(exc.retry_after_s or 5)
except AuthError:
    print("Check your server_key — authentication failed")
except ERLCError as exc:
    print("API error", exc.status_code, exc.error_code)
```

See [Errors and Troubleshooting](./Errors-and-Troubleshooting.md) for the full
exception hierarchy and diagnostics helpers.

## Utilities

The base import (`import erlc_api`) is intentionally small — only the clients,
models, errors, and command helpers load at import time. Utility modules are
opt-in explicit imports, keeping startup fast and dependencies light for apps
that only need basic API calls.

```python
# These are NOT loaded by `import erlc_api`
from erlc_api.find import Finder
from erlc_api.cache import AsyncCachedClient
from erlc_api.vehicles import VehicleTools
from erlc_api.multiserver import AsyncMultiServer
```

Optional extras (webhooks, export, rich display, scheduling, location maps)
must be installed separately. See [Installation and Extras](./Installation-and-Extras.md).

## Related Pages

- [Installation and Extras](./Installation-and-Extras.md)
- [Getting Started](./Getting-Started.md)
- [Clients and Authentication](./Clients-and-Authentication.md)
- [Typed vs Raw Responses](./Typed-vs-Raw-Responses.md)
- [Errors and Troubleshooting](./Errors-and-Troubleshooting.md)

---

[Previous Page: Installation and Extras](./Installation-and-Extras.md) | [Next Page: Getting Started](./Getting-Started.md)
