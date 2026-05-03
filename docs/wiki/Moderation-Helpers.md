# Moderation Helpers

Moderation helpers are thin workflows around the flexible command API. They do
not invent PRC permissions, bypass restrictions, or guarantee a command exists.
They compose commands, support dry-run previews, and provide simple audit text.

Async import:

```python
from erlc_api.moderation import AsyncModerator
```

Sync import:

```python
from erlc_api.moderation import Moderator
```

## AsyncModerator

Signature:

```python
AsyncModerator(api: Any, *, server_key: str | None = None)
```

Purpose: async helper for common command workflows.

Methods:

| Method | Return type | Purpose |
| --- | --- | --- |
| `command(command, *, dry_run=False)` | `CommandResult` | Execute or preview any command. |
| `preview(command)` | `str` | Normalize command without sending HTTP. |
| `pm(target, message, *, dry_run=False)` | `CommandResult` | Send `:pm target message`. |
| `warn(target, reason, *, dry_run=False)` | `CommandResult` | Send `:warn target reason`. |
| `ban(target, reason, duration=None, *, dry_run=False)` | `CommandResult` | Send `:ban target [duration] reason`. |
| `kick(target, reason=None, *, dry_run=False)` | `CommandResult` | Send `:kick target [reason]`. |
| `audit_message(action, target, *, moderator=None, reason=None)` | `str` | Build simple audit text. |

Minimal example:

```python
from erlc_api import AsyncERLC
from erlc_api.moderation import AsyncModerator

async with AsyncERLC("server-key") as api:
    mod = AsyncModerator(api)
    preview = await mod.preview("warn Avi RDM")
    result = await mod.warn("Avi", "RDM")
    print(preview, result.message)
```

Important options:

- `server_key=` binds the helper to a server when the client manages multiple keys.
- `dry_run=True` calls the client's command dry-run path.

Common mistakes:

- Treating `AsyncModerator.warn(...)` as a permission check. PRC still decides
  whether the command may run.
- Assuming duration syntax is universal. The helper only composes arguments.

## Moderator

Signature:

```python
Moderator(api: Any, *, server_key: str | None = None)
```

Purpose: sync version of `AsyncModerator`.

Methods: same names as `AsyncModerator`, without `await`.

Minimal example:

```python
from erlc_api import ERLC
from erlc_api.moderation import Moderator

with ERLC("server-key") as api:
    mod = Moderator(api)
    print(mod.pm("Avi", "hello").message)
```

Common mistakes:

- Using sync `Moderator` in async handlers. Use `AsyncModerator`.

## Dry-run Previews

Preview without sending HTTP:

```python
text = await AsyncModerator(api).preview("kick Avi")
print(text)  # :kick Avi
```

Dry-run through the command API:

```python
result = await AsyncModerator(api).warn("Avi", "RDM", dry_run=True)
print(result.success, result.raw["command"])
```

## Audit Messages

Signature:

```python
audit_message(action: str, target: str, *, moderator: str | None = None, reason: str | None = None) -> str
```

Purpose: build a compact human-readable audit line.

Example:

```python
message = Moderator(api).audit_message(
    "warned",
    "Avi",
    moderator="Console",
    reason="RDM",
)
```

Return value:

```text
warned Avi by Console: RDM
```

Common mistakes:

- Treating audit messages as persistent storage. Store them in your own logs or database if needed.

## Safer Custom Workflow

```python
from erlc_api.find import Finder
from erlc_api.moderation import AsyncModerator


async def warn_if_online(api, target: str, reason: str):
    player = Finder(await api.players()).player(target)
    if player is None:
        return None
    return await AsyncModerator(api).warn(player.name or target, reason)
```

This pattern keeps lookups explicit and leaves the command execution path simple.

## Related Pages

- [Earlier in the guide: Formatting, Analytics, and Export](./Formatting-Analytics-and-Export.md)
- [Next in the guide: Waiters and Watchers](./Waiters-and-Watchers.md)

---

[Previous Page: Formatting, Analytics, and Export](./Formatting-Analytics-and-Export.md) | [Next Page: Waiters and Watchers](./Waiters-and-Watchers.md)
