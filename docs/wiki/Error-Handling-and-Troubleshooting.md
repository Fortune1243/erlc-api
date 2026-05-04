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

## User-facing Diagnostics

Use `erlc_api.diagnostics` when errors need to become bot replies, dashboard
messages, or structured API responses:

```python
from erlc_api.diagnostics import diagnose_error

try:
    players = await api.players()
except Exception as exc:
    diagnostics = diagnose_error(exc)
    print(diagnostics.to_dict())
```

For Discord bots, pair diagnostics with dependency-free Discord payload helpers:

```python
from erlc_api.discord_tools import DiscordFormatter

try:
    players = await api.players()
except ERLCError as exc:
    diagnostics = diagnose_error(exc)
    await ctx.send(**DiscordFormatter().diagnostics(diagnostics).to_dict())
```

Diagnostics are for presentation. Keep typed exception handling for control
flow.

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
- Treating diagnostics as a retry policy. They explain problems; they do not
  retry requests.
- Expecting command flows to execute commands automatically.

## Related Pages

- [Errors and Rate Limits](./Errors-and-Rate-Limits.md)
- [Rate Limits, Retries, and Reliability](./Rate-Limits-Retries-and-Reliability.md)
- [Security and Secrets](./Security-and-Secrets.md)
- [Workflow Utilities Reference](./Workflow-Utilities-Reference.md)

---

[Previous Page: Errors and Rate Limits](./Errors-and-Rate-Limits.md) | [Next Page: Testing and Mocking](./Testing-and-Mocking.md)
