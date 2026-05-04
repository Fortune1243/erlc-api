# Clients and Authentication

`erlc-api.py` v2 exposes two public clients:

- `AsyncERLC` for async apps, bots, web backends, and workers.
- `ERLC` for sync scripts and command-line tools.

Both clients use the same flat method names. The only difference is whether you
`await` the call.

## AsyncERLC

Signature:

```python
AsyncERLC(
    server_key: str | None = None,
    *,
    global_key: str | None = None,
    base_url: str = "https://api.policeroleplay.community",
    timeout_s: float = 20.0,
    retry_429: bool = True,
    rate_limited: bool = True,
    user_agent: str | None = None,
)
```

Purpose: async PRC API client using `httpx.AsyncClient`.

Return type: client object. Endpoint methods return typed models by default.

Minimal example:

```python
from erlc_api import AsyncERLC

async with AsyncERLC("server-key") as api:
    players = await api.players()
    print(players)
```

Important options:

| Option | Purpose |
| --- | --- |
| `server_key` | Default PRC private server key. Can be omitted only if each call passes `server_key=`. |
| `global_key` | Optional large-app/global API key. Sent as `Authorization`. |
| `base_url` | Override API base URL for tests or custom gateways. |
| `timeout_s` | HTTP timeout in seconds. |
| `retry_429` | Sleep once and retry once on rate limits when retry timing is available. |
| `rate_limited` | Enable dynamic pre-request throttling based on PRC rate-limit headers. Defaults to `True`; pass `False` to opt out. |
| `user_agent` | Override default `erlc-api-python/<version>` user agent. |

Common mistakes:

- Creating a long-lived `AsyncERLC` without closing it. Use `async with`, or call `await api.close()`.
- Calling async methods from sync code without an event loop. Use `ERLC` for sync scripts.
- Passing the global key as `server_key`. The global key belongs in `global_key=`.

## ERLC

Signature:

```python
ERLC(
    server_key: str | None = None,
    *,
    global_key: str | None = None,
    base_url: str = "https://api.policeroleplay.community",
    timeout_s: float = 20.0,
    retry_429: bool = True,
    rate_limited: bool = True,
    user_agent: str | None = None,
)
```

Purpose: sync PRC API client using `httpx.Client`.

Return type: client object. Endpoint methods return typed models by default.

Minimal example:

```python
from erlc_api import ERLC

with ERLC("server-key") as api:
    print(api.server())
```

Common mistakes:

- Using `ERLC` inside an async Discord or FastAPI handler. Use `AsyncERLC` there.
- Forgetting to use `with ERLC(...)` for scripts that make several calls.

## Lifecycle

Async lifecycle:

```python
api = AsyncERLC("server-key")
await api.start()
try:
    players = await api.players()
finally:
    await api.close()
```

Sync lifecycle:

```python
api = ERLC("server-key")
api.start()
try:
    players = api.players()
finally:
    api.close()
```

Endpoint methods auto-start the underlying HTTP client if needed. Explicit
startup is still useful for app startup hooks and repeated calls.

## Dynamic Rate Limiting

`retry_429=True` reacts after PRC returns a rate limit. `rate_limited=True` is
the default and learns from successful and failed response headers before
avoidable requests:

```python
api = AsyncERLC("server-key")
players = await api.players()
snapshot = api.rate_limits
```

Pass `rate_limited=False` only when your application already coordinates rate
limits outside the wrapper.

`api.rate_limits` returns a `RateLimitSnapshot` when dynamic limiting is enabled,
or `None` when it is disabled. Requests made with a `global_key` are tracked
under the `"global"` scope; server-key-only requests are tracked under
`"server"`. The two scopes are independent and never share state.

## Authentication Headers

Every server request sends:

```text
Server-Key: <server key>
```

When `global_key=` is configured, requests also send:

```text
Authorization: <global key>
```

Custom headers passed to `request(..., headers=...)` cannot overwrite
`Server-Key` or `Authorization`; the client keeps those under its control.

## Per-call Server Key Override

Every endpoint method accepts `server_key=`.

Async:

```python
async with AsyncERLC("main-key") as api:
    main = await api.players()
    event = await api.players(server_key="event-server-key")
```

Sync:

```python
with ERLC("main-key") as api:
    main = api.players()
    event = api.players(server_key="event-server-key")
```

Use this for multi-server dashboards and bots. If neither the client nor the
method has a server key, the client raises `ValueError` before sending HTTP.

## Low-level Request

Async signature:

```python
await api.request(
    method: str,
    path: str,
    *,
    server_key: str | None = None,
    params: Mapping[str, Any] | None = None,
    json: Any = None,
    headers: Mapping[str, str] | None = None,
) -> Any
```

Sync signature:

```python
api.request(
    method: str,
    path: str,
    *,
    server_key: str | None = None,
    params: Mapping[str, Any] | None = None,
    json: Any = None,
    headers: Mapping[str, str] | None = None,
) -> Any
```

Purpose: raw escape hatch for newly added PRC endpoints or custom tests.

Minimal example:

```python
payload = await api.request("GET", "/v2/server", params={"Players": "true"})
```

Return type: decoded JSON when possible, response text for non-JSON responses,
or `None` for empty responses.

Common mistakes:

- Passing a path without a leading slash when your `base_url` expects one.
- Expecting typed dataclasses from `request`; this method intentionally returns raw data.

## Validation Helpers

`validate_key(*, server_key: str | None = None) -> ValidationResult`

Purpose: check whether a key can call `server(raw=True)` without raising common
API errors.

Return type:

```python
ValidationResult(
    status: ValidationStatus,
    retry_after: float | None = None,
    api_status: int | None = None,
)
```

Statuses:

| Status | Meaning |
| --- | --- |
| `ValidationStatus.OK` | Request succeeded. |
| `ValidationStatus.AUTH_ERROR` | Auth failed. |
| `ValidationStatus.RATE_LIMITED` | PRC returned a rate limit. |
| `ValidationStatus.NETWORK_ERROR` | Transport failed. |
| `ValidationStatus.API_ERROR` | PRC returned another API error. |

`health_check()` is an alias for `validate_key()`.

Async:

```python
result = await api.validate_key()
if result.status is ValidationStatus.OK:
    print("ready")
```

Sync:

```python
result = api.health_check()
print(result.status)
```

## Related Pages

- [Earlier in the guide: FAQ](./FAQ.md)
- [Next in the guide: Endpoint Reference](./Endpoint-Reference.md)

---

[Previous Page: FAQ](./FAQ.md) | [Next Page: Endpoint Reference](./Endpoint-Reference.md)
