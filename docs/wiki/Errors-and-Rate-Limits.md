# Errors and Rate Limits

All wrapper exceptions inherit from `ERLCError`.

```python
from erlc_api import ERLCError, RateLimitError

try:
    players = await api.players()
except RateLimitError as exc:
    print(exc.retry_after)
except ERLCError as exc:
    print(exc)
```

## Base Error Shape

`ERLCError` public members:

| Member | Type | Meaning |
| --- | --- | --- |
| `message` | `str` | Human-readable error message. |
| `method` | `str | None` | HTTP method or `DECODE`. |
| `path` | `str | None` | API path or decode endpoint label. |
| `status` | `int | None` | HTTP status code. |
| `status_code` | `int | None` | Alias for `status`. |
| `error_code` | `int | None` | PRC error code when present. |
| `body_excerpt` | `str | None` | Short response-body excerpt. |

Minimal example:

```python
except ERLCError as exc:
    print(exc.method, exc.path, exc.status_code, exc.error_code)
```

Common mistake: logging only `str(exc)` and discarding structured fields. Store
the attributes too when you build dashboards or alerts.

## Exception List

| Exception | Parent | Raised when |
| --- | --- | --- |
| `ERLCError` | `Exception` | Base class for wrapper failures. |
| `APIError` | `ERLCError` | Generic non-success PRC response. |
| `BadRequestError` | `APIError` | Status `400` or invalid request details. |
| `AuthError` | `APIError` | Status `403` or auth-related PRC codes. |
| `PermissionDeniedError` | `AuthError` | PRC says key lacks permission. |
| `NotFoundError` | `APIError` | Status `404`. |
| `NetworkError` | `ERLCError` | Timeout, DNS, connection, or request transport error. |
| `RateLimitError` | `APIError` | Status `429` or PRC rate-limit error code. |
| `InvalidCommandError` | `BadRequestError` | PRC command error code for invalid command. |
| `RestrictedCommandError` | `PermissionDeniedError` | PRC command is restricted from API execution. |
| `ProhibitedMessageError` | `BadRequestError` | PRC rejected message content. |
| `ServerOfflineError` | `APIError` | PRC reports server offline/unavailable. |
| `RobloxCommunicationError` | `APIError` | PRC/Roblox/module communication failure or server-side issue. |
| `ModuleOutdatedError` | `APIError` | In-game module is out of date. |
| `ModelDecodeError` | `ERLCError` | Typed decoding received an unexpected payload shape. |

## Error-code Mapping

The transport maps PRC error codes when present:

| PRC signal | Wrapper exception |
| --- | --- |
| Status `404` | `NotFoundError` |
| Status `429` or code `4001` | `RateLimitError` |
| Status `403` or codes `2000`, `2001`, `2002`, `2003`, `2004` | `AuthError` |
| Code `3001` | `InvalidCommandError` |
| Code `3002` or status `422` | `ServerOfflineError` |
| Code `4002` | `RestrictedCommandError` |
| Code `4003` | `ProhibitedMessageError` |
| Code `9998` | `PermissionDeniedError` |
| Code `9999` | `ModuleOutdatedError` |
| Codes `1001`, `1002`, or status `>=500` | `RobloxCommunicationError` |
| Status `400` | `BadRequestError` |
| Anything else non-success | `APIError` |

Common mistake: treating PRC error codes as stable business logic in your app.
Use wrapper exception classes where possible and log raw codes for diagnostics.

## RateLimitError

Extra members:

| Member | Type | Meaning |
| --- | --- | --- |
| `bucket` | `str | None` | Parsed from `X-RateLimit-Bucket`. |
| `retry_after` | `float | None` | Seconds from `Retry-After` or response body. |
| `retry_after_s` | `float | None` | Alias for `retry_after`. |
| `reset_epoch_s` | `float | None` | Parsed from `X-RateLimit-Reset`. |

Minimal example:

```python
from erlc_api import RateLimitError

try:
    await api.players()
except RateLimitError as exc:
    print("bucket", exc.bucket)
    print("retry after", exc.retry_after_s)
```

Important behavior:

- `retry_429=True` by default.
- The client retries at most once.
- It sleeps only when `Retry-After`, body retry data, or reset time provide timing.
- If the second attempt is also rate-limited, `RateLimitError` is raised.

Disable automatic retry:

```python
api = AsyncERLC("server-key", retry_429=False)
```

Sync:

```python
api = ERLC("server-key", retry_429=False)
```

Common mistakes:

- Assuming automatic retries make polling loops safe. Polling utilities still
  make API calls and can still be rate-limited.
- Sleeping forever. The wrapper sleeps only once.

## ModelDecodeError

Signature:

```python
ModelDecodeError(message: str, *, endpoint: str, expected: str, payload: Any)
```

Purpose: report unexpected payload shape while decoding typed models.

Extra members:

| Member | Type | Meaning |
| --- | --- | --- |
| `endpoint` | `str` | Endpoint label used by the decoder. |
| `expected` | `str` | Expected payload shape. |

Minimal example:

```python
from erlc_api import ModelDecodeError

try:
    players = await api.players()
except ModelDecodeError as exc:
    print(exc.endpoint, exc.expected, exc.body_excerpt)
```

Common mistake: retrying decode errors as if they were network failures. Inspect
the raw payload or use `raw=True` to see what PRC returned.

## Validation Helpers

`validate_key()` and `health_check()` convert common failures into
`ValidationResult`:

```python
result = await api.validate_key()
print(result.status, result.retry_after, result.api_status)
```

Statuses:

| Status | Meaning |
| --- | --- |
| `ValidationStatus.OK` | Key worked. |
| `ValidationStatus.AUTH_ERROR` | Auth failed. |
| `ValidationStatus.RATE_LIMITED` | Rate-limited. |
| `ValidationStatus.NETWORK_ERROR` | Transport failure. |
| `ValidationStatus.API_ERROR` | Other API error. |

Common mistake: using validation helpers for every request. They are for health
checks and setup flows; normal endpoint calls should use exceptions.

## Removed Ops Stack

v2 intentionally removed public cache, Redis, metrics, request replay, tracing,
circuit breaker, request coalescing, and retry-policy machinery. Keep those in
your application layer if you need them.
