# Commands Reference

`erlc-api.py` v2 uses flexible command syntax. You can pass plain strings, immutable
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

## `CommandPolicy`

Signature:

```python
CommandPolicy(
    *,
    allowed: Iterable[str] | str | None = None,
    blocked: Iterable[str] | str | None = None,
    max_length: int | None = 120,
    case_sensitive: bool = False,
)
```

Purpose: add a local allowlist-first safety layer before a bot, web route, or
custom-command handler calls `api.command(...)`.

Return types:

| Method | Return type | Purpose |
| --- | --- | --- |
| `check(command)` | `CommandPolicyResult` | Inspect whether a command would be allowed. |
| `validate(command)` | `str` | Return normalized command text or raise `CommandPolicyError`. |

Minimal example:

```python
from erlc_api import CommandPolicy, CommandPolicyError, cmd

policy = CommandPolicy(allowed={"h", "pm"}, max_length=120)

try:
    command_text = policy.validate(cmd.h("Short staff announcement"))
except CommandPolicyError as exc:
    print(exc.result.reason)
else:
    await api.command(command_text)
```

Important behavior:

- `CommandPolicy()` blocks everything until `allowed=` is configured.
- `blocked=` wins even if the same command appears in `allowed=`.
- `max_length` counts the normalized command including the leading `:`.
- The policy does not call PRC and does not invent Discord roles or PRC
  permissions.

Common mistakes:

- Calling `api.command(...)` with the original user input after validating a
  different command. Execute the normalized string returned by `validate()`.
- Treating `check()` as enforcement without checking `result.allowed`.
- Using policy as a replacement for Discord permissions, web auth, or audit
  logging.

## Command Metadata

Signature:

```python
get_command_metadata(command: str | Command) -> CommandMetadata | None
```

Purpose: expose lightweight local hints for known commands without restricting
`api.command(...)`.

Return type: `CommandMetadata | None`.

Minimal example:

```python
from erlc_api import PermissionLevel, get_command_metadata

meta = get_command_metadata(":pm Avi hello")
if meta is not None:
    print(meta.display_name, meta.category, meta.minimum_permission)
    assert meta.minimum_permission >= PermissionLevel.MOD
```

Metadata fields:

| Field | Purpose |
| --- | --- |
| `name` | Normalized command name without `:`. |
| `display_name` | Human-readable label for help text. |
| `category` | Broad docs/diagnostics category. |
| `minimum_permission` | Recommended `PermissionLevel` hint. |
| `supports_target` | Whether the command commonly targets a player. |
| `supports_multiple_targets` | Whether multiple targets may make sense. |
| `supports_text` | Whether trailing message text commonly makes sense. |

Important behavior: metadata is advisory. It helps command policies, Discord
help text, diagnostics, and analytics, but the wrapper still accepts flexible
commands and does not block unknown command names.

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
from erlc_api import AsyncERLC, CommandPolicy, cmd

async with AsyncERLC("server-key") as api:
    policy = CommandPolicy(allowed={"pm"}, max_length=120)
    result = await api.command(policy.validate(cmd.pm("Avi", "hello")))
    print(result.message)
```

Minimal sync example:

```python
from erlc_api import ERLC, CommandPolicy

with ERLC("server-key") as api:
    policy = CommandPolicy(allowed={"h"}, max_length=120)
    print(api.command(policy.validate("h hello")).message)
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
