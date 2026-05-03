# Commands Reference

`erlc-api` v2 uses flexible command syntax. You can pass plain strings, immutable
`Command` values, or the `cmd` factory.

## `normalize_command`

Signature:

```python
normalize_command(command: str | Command) -> str
```

Purpose: normalize a command to PRC format.

Return type: `str`.

Minimal example:

```python
from erlc_api import normalize_command

assert normalize_command("h hello") == ":h hello"
assert normalize_command(":h hello") == ":h hello"
```

Important behavior:

| Input | Output |
| --- | --- |
| `"h hi"` | `":h hi"` |
| `":h hi"` | `":h hi"` |
| `"  pm Avi hello  "` | `":pm Avi hello"` |

Common mistakes:

- Passing non-strings. Use `str(...)` yourself if you really want custom values.
- Passing a command with newline characters. Newlines are rejected.

## `validate_command`

Signature:

```python
validate_command(command: str | Command) -> None
```

Purpose: run the same minimal validation as `normalize_command`.

Return type: `None` on success.

Minimal example:

```python
from erlc_api import validate_command

validate_command("h server restart in 5 minutes")
```

Important options: none.

Common mistakes:

- Expecting PRC permission checks. Local validation only checks essential syntax.

## `Command`

Signature:

```python
Command(text: str)
```

Purpose: immutable command value accepted by `api.command(...)`.

Return type: `Command`.

Minimal example:

```python
from erlc_api import Command

announcement = Command("h hello")
assert str(announcement) == ":h hello"
```

Important options: none.

Common mistakes:

- Mutating command text after creation. `Command` is frozen.

## `cmd`

`cmd` is a `CommandFactory` instance exported from `erlc_api`.

Signatures:

```python
cmd(name: str, *parts: Any) -> Command
cmd.raw(command: str) -> Command
cmd.<command_name>(*parts: Any) -> Command
```

Purpose: build commands without rigid helper classes.

Return type: `Command`.

Minimal examples:

```python
from erlc_api import cmd

await api.command(cmd.h("hello"))
await api.command(cmd.pm("Player", "hello"))
await api.command(cmd("pm", "Player", "hello"))
await api.command(cmd.raw(":h already normalized"))
```

Important behavior:

- Attribute access is dynamic. `cmd.warn(...)`, `cmd.kick(...)`, and
  `cmd.anything(...)` all build a command name.
- Blank command parts raise `ValueError`.
- Parts are joined with spaces.

Common mistakes:

- Expecting a hard-coded command allowlist. v2 avoids rigid command helpers.
- Passing player/message parts that contain leading/trailing whitespace and
  expecting it to be preserved. Parts are stripped.

## `api.command`

Async signature:

```python
await api.command(
    command: str | Command,
    *,
    server_key: str | None = None,
    raw: bool = False,
    dry_run: bool = False,
) -> CommandResult
```

Sync signature:

```python
api.command(
    command: str | Command,
    *,
    server_key: str | None = None,
    raw: bool = False,
    dry_run: bool = False,
) -> CommandResult
```

Purpose: send a v2 PRC server command.

Return type: `CommandResult` by default, raw payload with `raw=True`.

Minimal async example:

```python
from erlc_api import AsyncERLC, cmd

async with AsyncERLC("server-key") as api:
    result = await api.command(cmd.pm("Avi", "hello"))
    print(result.message)
```

Minimal sync example:

```python
from erlc_api import ERLC

with ERLC("server-key") as api:
    print(api.command("h hello").message)
```

Important options:

| Option | Purpose |
| --- | --- |
| `server_key=` | Override the client's default server key. |
| `raw=True` | Return exact PRC JSON. |
| `dry_run=True` | Validate and return a local result without sending HTTP. |

Dry-run:

```python
preview = await api.command("pm Avi hello", dry_run=True)
print(preview.raw["command"])
```

Common mistakes:

- Using `dry_run=True` as a PRC permission check. It only checks local syntax.
- Assuming `result.success` is always boolean. It can be `None` when PRC only
  returns a message.

## Validation Rules

The wrapper validates only essentials:

| Rule | Failure |
| --- | --- |
| Command must be `str` or `Command` | `TypeError` |
| Command cannot be blank | `ValueError` |
| Command cannot contain `\n` or `\r` | `ValueError` |
| Command must have a name after `:` | `ValueError` |

The wrapper does not hard-block `:log` and does not maintain a command denylist.
PRC remains the source of truth for permissions and restricted commands.

## Command Errors

PRC command errors map to typed exceptions:

| Exception | Meaning |
| --- | --- |
| `InvalidCommandError` | Command is missing, malformed, or invalid. |
| `RestrictedCommandError` | Command is restricted from API execution. |
| `ProhibitedMessageError` | Message content was rejected. |
| `PermissionDeniedError` | Key cannot execute the action. |

Example:

```python
from erlc_api import ERLCError, InvalidCommandError

try:
    await api.command("unknown")
except InvalidCommandError as exc:
    print(exc.message)
except ERLCError as exc:
    print(exc)
```

## Related Utilities

Use moderation helpers when you want reusable workflows around command
composition:

```python
from erlc_api.moderation import AsyncModerator

moderator = AsyncModerator(api)
await moderator.warn("Player", "RDM")
```

See [Moderation Helpers](./Moderation-Helpers.md).

## Related Pages

- [Earlier in the guide: Typed vs Raw Responses](./Typed-vs-Raw-Responses.md)
- [Next in the guide: Function List](./Function-List.md)

---

[Previous Page: Typed vs Raw Responses](./Typed-vs-Raw-Responses.md) | [Next Page: Function List](./Function-List.md)
