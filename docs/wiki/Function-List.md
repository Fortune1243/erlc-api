# Function List

## Clients

- `AsyncERLC(server_key=None, global_key=None, rate_limited=True)`
- `ERLC(server_key=None, global_key=None, rate_limited=True)`
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
- `CommandPolicy(allowed={"h", "pm"}, max_length=120)`
- `CommandPolicy.check(command)` / `CommandPolicy.validate(command)`
- `CommandPolicyResult`
- `CommandPolicyError`

## Security

- `from erlc_api.security import key_fingerprint`

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
- `from erlc_api.snapshot import SnapshotStore`
- `from erlc_api.audit import AuditEvent, AuditLog`
- `from erlc_api.idempotency import MemoryDeduper, FileDeduper`
- `from erlc_api.limits import PollPlan, poll_plan, safe_interval`
- `from erlc_api.ratelimit import AsyncRateLimiter, RateLimiter`
- `from erlc_api.error_codes import explain_error_code, list_error_codes`
- `from erlc_api.custom_commands import CustomCommandRouter`
- `from erlc_api.location import LocationTools, MapRenderer`
- `from erlc_api.bundle import AsyncBundle, Bundle, BundleRequest`
- `from erlc_api.rules import RuleEngine, AsyncRuleEngine, Conditions`
- `from erlc_api.multiserver import AsyncMultiServer, MultiServer, ServerRef`
- `from erlc_api.discord_tools import DiscordFormatter, DiscordEmbed`
- `from erlc_api.diagnostics import diagnose_error, diagnose_status`
- `from erlc_api.cache import AsyncCachedClient, CachedClient, MemoryCache`
- `from erlc_api.status import AsyncStatus, Status, StatusBuilder`
- `from erlc_api.command_flows import CommandFlowBuilder, CommandTemplate`
- Legacy grouped helpers remain under `erlc_api.utils`, `erlc_api.web`, `erlc_api.discord`, and `erlc_api.webhooks`.

Utilities are not imported by top-level `import erlc_api`.

## Related Pages

- [Earlier in the guide: Commands Reference](./Commands-Reference.md)
- [Next in the guide: Utilities Reference](./Utilities-Reference.md)

---

[Previous Page: Commands Reference](./Commands-Reference.md) | [Next Page: Utilities Reference](./Utilities-Reference.md)
