# Rate Limits, Retries, and Reliability

The wrapper keeps reliability behavior intentionally small. It parses PRC
rate-limit metadata, raises typed errors, optionally performs one safe retry on
`429`, and can opt in to dynamic pre-request limiting with `rate_limited=True`.
It does not include cache backends, circuit breakers, tracing, metrics sinks,
request replay, or request coalescing.

## Request Headers

Every server request sends:

- `Server-Key`: the per-server API key.
- `Authorization`: only when `global_key=` is configured.
- `User-Agent`: wrapper version and Python runtime by default.

## 429 Behavior

On a `429`, the transport raises `RateLimitError`.

```python
from erlc_api import RateLimitError

try:
    await api.players()
except RateLimitError as exc:
    print(exc.retry_after_s, exc.reset_epoch_s, exc.bucket)
```

Useful fields:

| Field | Meaning |
| --- | --- |
| `retry_after_s` | Seconds to wait, parsed from headers or body when available. |
| `reset_epoch_s` | Epoch reset time parsed from rate-limit headers. |
| `bucket` | PRC bucket name when provided. |
| `error_code` | PRC error code when present. |
| `body_excerpt` | Short safe body excerpt for diagnostics. |

## Retry Policy

Default constructor behavior:

```python
api = AsyncERLC("server-key", retry_429=True)
```

When timing information exists, the wrapper sleeps once and retries once. It
does not perform exponential backoff or infinite retries.

Disable the built-in retry when your app has its own scheduler:

```python
api = AsyncERLC("server-key", retry_429=False)
```

## Dynamic Rate Limiter

Enable dynamic limiting when your app polls or has bursty command handlers:

```python
api = AsyncERLC("server-key", rate_limited=True)
```

Behavior:

- learns from `X-RateLimit-*` and `Retry-After` headers on every response;
- waits before requests when an observed bucket has no remaining capacity until
  reset;
- updates state from actual `429` responses;
- tracks global-key requests separately from server-key-only requests;
- stores state in memory only.

Inspect current state:

```python
snapshot = api.rate_limits
if snapshot is not None:
    print(snapshot.to_dict())
```

Use `erlc_api.ratelimit` directly only for custom transports:

```python
from erlc_api.ratelimit import AsyncRateLimiter

limiter = AsyncRateLimiter()
```

## Polling Guidance

Use `erlc_api.limits` for conservative planning:

```python
from erlc_api.limits import poll_plan

plan = poll_plan(server_count=2, endpoint_count=3, timeout_s=120)
```

This module does not claim official PRC rate limits. It only helps avoid overly
aggressive polling in your own app.

## Reliability Boundaries

The wrapper handles:

- decoding successful responses;
- mapping known error codes to typed exceptions;
- parsing rate-limit metadata;
- optional dynamic pre-request waiting when `rate_limited=True`;
- closing sync and async HTTP clients.

Your application should handle:

- persistence and retries across process restarts;
- user-visible degraded status;
- queueing high-volume bot commands;
- idempotency for webhook delivery.

## Common Mistakes

- Running many watchers at one-second intervals across multiple servers.
- Treating `retry_429=True` as a full retry policy.
- Expecting `rate_limited=True` to coordinate multiple Python processes.
- Swallowing `RateLimitError` without slowing future calls.
- Assuming advisory `safe_interval()` values are official PRC limits.

## Related Pages

- [Errors and Rate Limits](./Errors-and-Rate-Limits.md)
- [Ops Utilities Reference](./Ops-Utilities-Reference.md)
- [Waiters and Watchers](./Waiters-and-Watchers.md)

---

[Previous Page: Security and Secrets](./Security-and-Secrets.md) | [Next Page: Errors and Rate Limits](./Errors-and-Rate-Limits.md)
