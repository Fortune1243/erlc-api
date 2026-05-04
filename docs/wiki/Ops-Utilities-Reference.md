# Ops Utilities Reference

Ops utilities help applications persist snapshots, audit actions, deduplicate
events, plan polling intervals, and route PRC custom commands. They are lazy,
stdlib-first modules and are not imported by top-level `import erlc_api`.

## SnapshotStore

Import:

```python
from erlc_api.snapshot import SnapshotStore
```

Signature:

```python
SnapshotStore(path)
```

Purpose: append JSON-safe server snapshots to JSONL and compare current data
with the latest stored snapshot.

Example:

```python
store = SnapshotStore("server-snapshots.jsonl")
bundle = await api.server(all=True)

diff = store.diff_latest(bundle)
if diff.changed:
    store.save(bundle)
```

Key methods: `save()`, `latest()`, `history()`, `diff_latest()`, `prune()`.

## AuditLog

Import:

```python
from erlc_api.audit import AuditEvent, AuditLog
```

Purpose: create JSON-safe audit records from command results, webhook events,
watcher events, and moderation actions.

Example:

```python
audit = AuditLog("audit.jsonl")
result = await api.command("warn Player RDM")
event = audit.command_result(result, command=":warn Player RDM", actor="Console", target="Player")
print(event.to_console())
```

Use audit records for moderation review and operational timelines. Do not store
server keys or authorization headers in audit metadata.

## Idempotency

Imports:

```python
from erlc_api.idempotency import FileDeduper, MemoryDeduper
```

Purpose: avoid processing duplicate webhook deliveries or repeated watcher
events.

Example:

```python
dedupe = FileDeduper("webhook-dedupe.json", ttl_s=300)
if dedupe.check_and_mark(event_id):
    return {"ignored": True}
```

Use `MemoryDeduper` for one-process apps and `FileDeduper` for simple restart
tolerance.

## Poll Planning

Import:

```python
from erlc_api.limits import poll_plan, safe_interval
```

Purpose: produce conservative polling intervals based on server and endpoint
fanout.

```python
plan = poll_plan(server_count=2, endpoint_count=3, timeout_s=120)
```

These helpers are advisory. They are not official PRC rate-limit enforcement.

## Dynamic Rate Limiting

Imports:

```python
from erlc_api.ratelimit import AsyncRateLimiter, RateLimiter, RateLimitState, RateLimitSnapshot
```

Purpose: track PRC rate-limit headers in memory and wait before avoidable
requests. Most users enable it through the client constructor (`rate_limited=True`
is the default):

```python
api = AsyncERLC("server-key")
await api.players()
print(api.rate_limits.to_dict())
```

Use `AsyncRateLimiter` or `RateLimiter` directly only when building a custom
HTTP transport. Both share the same interface; `AsyncRateLimiter.before_request`
is a coroutine and uses `asyncio.Lock`; `RateLimiter.before_request` is
synchronous and uses `threading.Lock`.

### Public interface

| Method | Class | Returns | Purpose |
| --- | --- | --- | --- |
| `async before_request(method, path, *, key_scope="server", bucket=None)` | `AsyncRateLimiter` | `float` | Acquire the per-bucket async lock, sleep if a reset window is active, return seconds waited. |
| `before_request(method, path, *, key_scope="server", bucket=None)` | `RateLimiter` | `float` | Synchronous equivalent using a threading lock. |
| `after_response(method, path, headers, *, key_scope="server")` | Both | `RateLimitState \| None` | Parse `X-RateLimit-*` and `Retry-After` headers and store a `RateLimitState`. Returns `None` when no rate-limit headers are present. |
| `after_error(error, *, method=None, path=None, key_scope="server")` | Both | `RateLimitState \| None` | Store backoff state from a `RateLimitError`. Returns `None` for non-rate-limit errors. |
| `snapshot()` | Both | `RateLimitSnapshot` | Return a snapshot of all stored states, sorted by scope and bucket. |
| `reset()` | Both | `None` | Clear all stored state and route-to-bucket mappings. |

### RateLimitState fields

| Field | Type | Meaning |
| --- | --- | --- |
| `bucket` | `str` | Bucket name from `X-RateLimit-Bucket`, or `"METHOD /path"` route key when no bucket header was present (e.g. `"GET /v2/server"`). |
| `limit` | `int \| None` | Request limit from `X-RateLimit-Limit`. |
| `remaining` | `int \| None` | Remaining requests from `X-RateLimit-Remaining`. |
| `reset_epoch_s` | `float \| None` | Unix epoch reset time from `X-RateLimit-Reset`. |
| `retry_after_s` | `float \| None` | Seconds until retry from `Retry-After`. |
| `key_scope` | `str \| None` | Server key scope (usually `"server"`). |

Example for a custom transport:

```python
from erlc_api.ratelimit import AsyncRateLimiter

limiter = AsyncRateLimiter()

async def send(method: str, path: str, headers: dict) -> ...:
    await limiter.before_request(method, path)
    response = await http_client.request(method, path)
    limiter.after_response(method, path, response.headers)
    return response
```

Limiter state is process-local and memory-only. Multiple processes sharing a
server key need external coordination.

## Error Codes

Import:

```python
from erlc_api.error_codes import explain_error_code, list_error_codes
```

Purpose: explain PRC error codes without needing to trigger a failed request.

```python
info = explain_error_code(4001)
print(info.exception.__name__, info.retryable, info.advice)
```

The HTTP transport uses the same mapping table for typed exceptions.

## Custom Commands

Import:

```python
from erlc_api.custom_commands import CustomCommandRouter
```

Purpose: route PRC Event Webhook messages that start with `;`.

```python
router = CustomCommandRouter(prefix=";")


@router.command("ping", "p")
async def ping(ctx):
    return ctx.reply("pong")
```

Use `erlc_api.webhooks` for signature verification before dispatching to the
custom command router.

## Common Mistakes

- Treating `safe_interval()` as an official PRC limit.
- Expecting the process-local rate limiter to coordinate across multiple processes.
- Treating error-code advice as a replacement for catching typed exceptions.
- Using in-memory dedupe when duplicate protection must survive restarts.
- Logging secrets inside audit metadata.
- Making custom command handlers depend on a specific web or Discord framework.

## Related Pages

- [Utilities Reference](./Utilities-Reference.md)
- [Workflow Utilities Reference](./Workflow-Utilities-Reference.md)
- [Custom Commands Reference](./Custom-Commands-Reference.md)
- [Rate Limits, Retries, and Reliability](./Rate-Limits-Retries-and-Reliability.md)

---

[Previous Page: Wanted Stars](./Wanted-Stars.md) | [Next Page: Workflow Utilities Reference](./Workflow-Utilities-Reference.md)
