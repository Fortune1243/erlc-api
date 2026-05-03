# Function List

## Clients

- `AsyncERLC(server_key=None, global_key=None)`
- `ERLC(server_key=None, global_key=None)`
- `start()` / `close()`
- async and sync context-manager support
- `validate_key()` / `health_check()`

## Flat API Methods

All methods accept `server_key=` and `raw=True`.

- `server(players=False, staff=False, join_logs=False, queue=False, kill_logs=False, command_logs=False, mod_calls=False, emergency_calls=False, vehicles=False, all=False, include=None)`
- `players()`
- `staff()`
- `queue()`
- `join_logs()`
- `kill_logs()`
- `command_logs()`
- `mod_calls()`
- `emergency_calls()`
- `vehicles()`
- `bans()`
- `command(command, dry_run=False)`
- `request(method, path, params=None, json=None, headers=None)`

## Commands

- `cmd.h("message")`
- `cmd.pm("Player", "message")`
- `cmd("pm", "Player", "message")`
- plain strings such as `"h hello"` or `":h hello"`

## Utilities

- `from erlc_api.find import Finder`
- `from erlc_api.filter import Filter`
- `from erlc_api.sort import Sorter`
- `from erlc_api.group import Grouper`
- `from erlc_api.diff import Differ`
- `from erlc_api.wait import AsyncWaiter, Waiter`
- `from erlc_api.watch import AsyncWatcher, Watcher`
- `from erlc_api.format import Formatter`
- `from erlc_api.analytics import Analyzer`
- `from erlc_api.export import Exporter`
- `from erlc_api.moderation import AsyncModerator, Moderator`
- `from erlc_api.time import TimeTools`
- `from erlc_api.schema import SchemaInspector`
- Legacy grouped helpers remain under `erlc_api.utils`, `erlc_api.web`, `erlc_api.discord`, and `erlc_api.webhooks`.

Utilities are not imported by top-level `import erlc_api`.
