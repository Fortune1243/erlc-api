# Errors and Troubleshooting

All wrapper exceptions inherit from `ERLCError`, so you can always catch them
with one clause. The transport maps PRC HTTP status codes and PRC error codes to
typed Python exceptions before your code sees them. Catch the most specific
exception first, then fall back to `ERLCError` for anything unexpected. See the
exception list and diagnostics helpers below for structured error handling.

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

The same table is public:

```python
from erlc_api.error_codes import explain_error_code

info = explain_error_code(4001)
print(info.name, info.exception.__name__, info.advice)
```

Common mistake: treating PRC error codes as stable business logic in your app.
Use wrapper exception classes where possible and log raw codes for diagnostics.

## Error-code Utility

Import:

```python
from erlc_api.error_codes import exception_for_error_code, explain_error_code, list_error_codes
```

Public helpers:

| Helper | Return type | Purpose |
| --- | --- | --- |
| `explain_error_code(code_or_error)` | `ErrorCodeInfo | None` | Explain a code, mapping, exception, retry flag, and advice. |
| `list_error_codes(category=None)` | `list[ErrorCodeInfo]` | List known codes, optionally by category. |
| `exception_for_error_code(code, status=None)` | `type[APIError]` | Return the wrapper exception class for a code/status. |

`ErrorCodeInfo.to_dict()` returns JSON-safe data for dashboards or docs.

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

```python
except ERLCError as exc:
    print(exc.method, exc.path, exc.status_code, exc.error_code)
```

Common mistake: logging only `str(exc)` and discarding structured fields. Store
the attributes too when you build dashboards or alerts.

## RateLimitError

Extra members:

| Member | Type | Meaning |
| --- | --- | --- |
| `bucket` | `str | None` | Parsed from `X-RateLimit-Bucket`. |
| `retry_after` | `float | None` | Seconds from `Retry-After` or response body. |
| `retry_after_s` | `float | None` | Alias for `retry_after`. |
| `reset_epoch_s` | `float | None` | Parsed from `X-RateLimit-Reset`. |

```python
from erlc_api import RateLimitError

try:
    await client.players()
except RateLimitError as exc:
    print("bucket", exc.bucket)
    print("retry after", exc.retry_after_s)
```

Important behavior:

- `retry_429=True` by default.
- The client retries at most once.
- It sleeps only when `Retry-After`, body retry data, or reset time provide timing.
- If the second attempt is also rate-limited, `RateLimitError` is raised.
- `rate_limited=True` is enabled by default and waits before requests using
  observed headers.

Disable automatic retry:

```python
from erlc_api import AsyncERLC, ERLC

api = AsyncERLC("server-key", retry_429=False)  # async
api = ERLC("server-key", retry_429=False)       # sync
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

```python
from erlc_api import ModelDecodeError

try:
    players = await client.players()
except ModelDecodeError as exc:
    print(exc.endpoint, exc.expected, exc.body_excerpt)
```

Common mistake: retrying decode errors as if they were network failures. Inspect
the raw payload or use `raw=True` to see what PRC returned.

## Validation Helpers

`validate_key()` and `health_check()` convert common failures into
`ValidationResult`:

```python
result = await client.validate_key()
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

## Basic Handling Pattern

```python
from erlc_api import ERLCError, RateLimitError


try:
    players = await client.players()
except RateLimitError as exc:
    print("retry later", exc.retry_after_s, exc.bucket)
except ERLCError as exc:
    print("request failed", exc.status_code, exc.error_code, exc.body_excerpt)
else:
    print("players", len(players))
```

Catch specific exceptions first, then `ERLCError` as the shared base.

## Common Exceptions and First Steps

| Exception | Typical cause | First check |
| --- | --- | --- |
| `AuthError` | Missing, invalid, banned, or unauthorized key | Confirm `server_key` and optional `global_key`. |
| `PermissionDeniedError` | Key cannot access the resource | Confirm PRC permissions for that key. |
| `RateLimitError` | PRC returned `429` or rate-limit code | Use retry metadata and slow polling. |
| `InvalidCommandError` | PRC rejected command syntax or payload | Print the normalized command in dry-run first. |
| `RestrictedCommandError` | Command is not allowed through API | Use a different moderation flow. |
| `ProhibitedMessageError` | PRC rejected command text | Inspect content rules and message text. |
| `ServerOfflineError` | Server is offline or unreachable | Retry later or show offline status. |
| `RobloxCommunicationError` | PRC cannot communicate with Roblox/module | Treat as temporary unless repeated. |
| `ModuleOutdatedError` | In-game module needs update | Update the ER:LC module. |
| `ModelDecodeError` | Payload shape did not match models | Retry with `raw=True` and inspect `.body_excerpt`. |

## User-facing Diagnostics

Use `erlc_api.diagnostics` when errors need to become bot replies, dashboard
messages, or structured API responses:

```python
from erlc_api.diagnostics import diagnose_error

try:
    players = await client.players()
except Exception as exc:
    diagnostics = diagnose_error(exc)
    print(diagnostics.to_dict())
```

For Discord bots, pair diagnostics with dependency-free Discord payload helpers:

```python
from erlc_api.discord_tools import DiscordFormatter

try:
    players = await client.players()
except ERLCError as exc:
    diagnostics = diagnose_error(exc)
    await ctx.send(**DiscordFormatter().diagnostics(diagnostics).to_dict())
```

Diagnostics are for presentation. Keep typed exception handling for control
flow.

## Troubleshooting Auth

```python
result = await client.validate_key()
print(result.ok, result.status, result.message)
```

Use `validate_key()` for setup screens and diagnostics. It returns a
`ValidationResult` instead of raising common API errors.

## Troubleshooting Commands

```python
from erlc_api import cmd

preview = await client.command(cmd.pm("Player", "hello"), dry_run=True)
print(preview.raw["command"])
```

If dry-run looks correct but PRC rejects the command, handle the specific
command exception and show a user-facing message.

Use command flows when a moderation tool needs to preview multiple commands
before a human confirms them:

```python
from erlc_api.command_flows import CommandFlowBuilder

flow = (
    CommandFlowBuilder("warn-and-pm")
    .step("warn Avi RDM")
    .step("pm Avi Please read the rules")
    .build()
)

print(flow.preview())
```

Flows validate and preview only. They never send commands.

## Troubleshooting Models

If typed decoding fails:

```python
payload = await client.players(raw=True)
print(payload)
```

Report unexpected payloads with the endpoint, wrapper version, and a redacted
sample. Do not log server keys or authorization headers.

## Removed Ops Stack

v2 intentionally removed public cache, Redis, metrics, request replay, tracing,
circuit breaker, request coalescing, and retry-policy machinery. Keep those in
your application layer if you need them.

## Common Mistakes

- Catching only `Exception` and losing useful retry/auth context.
- Retrying every error as if it were a network failure.
- Logging complete headers or request objects with secrets.
- Assuming all non-200 responses are rate limits.
- Treating diagnostics as a retry policy. They explain problems; they do not
  retry requests.
- Expecting command flows to execute commands automatically.
- Logging only `str(exc)` and discarding structured fields like `status_code` and `error_code`.
- Retrying decode errors as if they were network failures.
- Using validation helpers for every request instead of only setup/health checks.

## Related Pages

- [Rate Limits, Retries, and Reliability](./Rate-Limits-Retries-and-Reliability.md)
- [Security and Secrets](./Security-and-Secrets.md)
- [Testing and Mocking](./Testing-and-Mocking.md)
- [Workflow Utilities Reference](./Workflow-Utilities-Reference.md)

---

[Previous Page: Scaling Your App](./Scaling-Your-App.md) | [Next Page: Testing and Mocking](./Testing-and-Mocking.md)
