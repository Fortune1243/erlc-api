# Error Handling and Troubleshooting

The wrapper exposes typed exceptions so applications can separate retryable
transport issues, auth problems, command rejections, rate limits, and model
decode failures.

## Basic Pattern

```python
from erlc_api import ERLCError, RateLimitError


try:
    players = await api.players()
except RateLimitError as exc:
    print("retry later", exc.retry_after_s, exc.bucket)
except ERLCError as exc:
    print("request failed", exc.status_code, exc.error_code, exc.body_excerpt)
else:
    print("players", len(players))
```

Catch specific exceptions first, then `ERLCError` as the shared base.

## Common Exceptions

| Exception | Typical cause | First check |
| --- | --- | --- |
| `AuthError` | Missing, invalid, banned, or unauthorized key | Confirm `Server-Key` and optional `global_key`. |
| `PermissionDeniedError` | Key cannot access the resource | Confirm PRC permissions for that key. |
| `RateLimitError` | PRC returned `429` or rate-limit code | Use retry metadata and slow polling. |
| `InvalidCommandError` | PRC rejected command syntax or payload | Print the normalized command in dry-run first. |
| `RestrictedCommandError` | Command is not allowed through API | Use a different moderation flow. |
| `ProhibitedMessageError` | PRC rejected command text | Inspect content rules and message text. |
| `ServerOfflineError` | Server is offline or unreachable | Retry later or show offline status. |
| `RobloxCommunicationError` | PRC cannot communicate with Roblox/module | Treat as temporary unless repeated. |
| `ModuleOutdatedError` | In-game module needs update | Update the ER:LC module. |
| `ModelDecodeError` | Payload shape did not match models | Retry with `raw=True` and inspect `.body_excerpt`. |

## Troubleshooting Auth

```python
result = await api.validate_key()
print(result.ok, result.status, result.message)
```

Use `validate_key()` for setup screens and diagnostics. It returns a
`ValidationResult` instead of raising common API errors.

## Troubleshooting Commands

```python
from erlc_api import cmd

preview = await api.command(cmd.pm("Player", "hello"), dry_run=True)
print(preview.raw["command"])
```

If dry-run looks correct but PRC rejects the command, handle the specific
command exception and show a user-facing message.

## Troubleshooting Models

If typed decoding fails:

```python
payload = await api.players(raw=True)
print(payload)
```

Report unexpected payloads with the endpoint, wrapper version, and a redacted
sample. Do not log server keys or authorization headers.

## Common Mistakes

- Catching only `Exception` and losing useful retry/auth context.
- Retrying every error as if it were a network failure.
- Logging complete headers or request objects with secrets.
- Assuming all non-200 responses are rate limits.

## Related Pages

- [Errors and Rate Limits](./Errors-and-Rate-Limits.md)
- [Rate Limits, Retries, and Reliability](./Rate-Limits-Retries-and-Reliability.md)
- [Security and Secrets](./Security-and-Secrets.md)

---

[Previous Page: Errors and Rate Limits](./Errors-and-Rate-Limits.md) | [Next Page: Testing and Mocking](./Testing-and-Mocking.md)
