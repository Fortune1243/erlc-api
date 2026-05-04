# Formatting, Analytics, and Export

These utilities are pure helpers. They do not call the API unless you pass them
data that was fetched elsewhere.

Imports:

```python
from erlc_api.format import Formatter
from erlc_api.analytics import Analyzer
from erlc_api.export import Exporter
```

For Discord embed/message payload dictionaries, use the 2.3 workflow module:

```python
from erlc_api.discord_tools import DiscordFormatter
```

## Formatter

Signature:

```python
Formatter(*, max_length: int | None = None)
```

Purpose: compact text output for Discord, console, logs, and optional Rich
tables.

Methods:

| Method | Return type | Purpose |
| --- | --- | --- |
| `player(player)` | `str` | One player line with name, ID, and team. |
| `players(players)` | `str` | Multi-line player list. |
| `queue(queue)` | `str` | Numbered queue user IDs. |
| `server(bundle)` | `str` | Server name and player count. |
| `logs(logs)` | `str` | Compact timestamp/actor/command lines. |
| `vehicles(vehicles)` | `str` | Vehicle name and owner lines. |
| `staff(staff)` | `str` | Staff role and name/user ID lines. |
| `error(error)` | `str` | Stringified exception, clipped if needed. |
| `command_result(result)` | `str` | `ok`, `failed`, or `unknown` plus message. |
| `discord(value)` | `str` | Discord-safe text with mass mentions neutralized. |
| `rich_table(items)` | `rich.table.Table` | Optional Rich table. |

Minimal example:

```python
from erlc_api.format import Formatter

fmt = Formatter(max_length=1900)
message = fmt.discord(fmt.players(await api.players()))
```

Important options:

- `max_length` clips output with `...`.
- `discord()` neutralizes `@everyone` and `@here`.

Optional extra:

```bash
pip install "erlc-api.py[rich]"
```

Required only for:

```python
table = Formatter().rich_table(await api.players())
```

Common mistakes:

- Assuming `Formatter` paginates Discord messages. It clips text; if you need
  pagination, split the returned string in your bot.

## DiscordFormatter

Import:

```python
from erlc_api.discord_tools import DiscordFormatter, DiscordEmbed, DiscordMessage
```

Purpose: create Discord-compatible dictionaries without importing `discord.py`.

Methods:

| Method | Return type | Purpose |
| --- | --- | --- |
| `server_status(status)` | `DiscordMessage` | Embed for a typed `ServerStatus`. |
| `players(players)` | `DiscordMessage` | Embed listing players and teams. |
| `queue(queue)` | `DiscordMessage` | Embed listing queued user IDs. |
| `diagnostics(diagnostics)` | `DiscordMessage` | Embed for diagnostics. |
| `error(error)` | `DiscordMessage` | Error embed. |
| `command_result(result)` | `DiscordMessage` | Command result embed. |

Minimal example:

```python
from erlc_api.discord_tools import DiscordFormatter
from erlc_api.status import StatusBuilder

bundle = await api.server(players=True, staff=True, queue=True, vehicles=True, emergency_calls=True)
status = StatusBuilder(bundle).build()
await channel.send(**DiscordFormatter().server_status(status).to_dict())
```

Important behavior:

- output is plain dictionaries, not `discord.py` objects;
- `@everyone` and `@here` are neutralized;
- content, field, title, and description lengths are clipped to Discord limits.

## Analyzer

Signature:

```python
Analyzer(data: Any)
```

Purpose: small summaries for dashboards, audits, and moderation views.

Methods:

| Method | Return type | Purpose |
| --- | --- | --- |
| `dashboard()` | `DashboardSummary` | Counts and common distributions. |
| `team_distribution()` | `dict[str, int]` | Player count by team. |
| `command_usage()` | `dict[str, int]` | Command log count by command name. |
| `staff_activity()` | `dict[str, int]` | Activity count from command logs and mod calls. |
| `moderation_trends()` | `dict[str, int]` | Counts for moderation-like commands and mod calls. |
| `peak_counts(snapshots=None)` | `dict[str, int]` | Peak player and queue counts. |

`DashboardSummary` fields:

| Field | Type |
| --- | --- |
| `player_count` | `int` |
| `queue_count` | `int` |
| `staff_count` | `int` |
| `vehicle_count` | `int` |
| `emergency_call_count` | `int` |
| `players_by_team` | `dict[str, int]` |
| `staff_by_role` | `dict[str, int]` |
| `vehicles_by_owner` | `dict[str, int]` |

Minimal example:

```python
from erlc_api.analytics import Analyzer
from erlc_api.discord_tools import DiscordFormatter
from erlc_api.status import StatusBuilder

bundle = await api.server(all=True)
summary = Analyzer(bundle).dashboard()
print(summary.player_count, summary.players_by_team)

status = StatusBuilder(bundle).build()
payload = DiscordFormatter().server_status(status).to_dict()
```

Important options:

- `Analyzer` works best with `server(all=True)` or lists of logs/snapshots.
- Missing sections are treated as empty collections.

Common mistakes:

- Treating analytics as authoritative moderation audit logs. It summarizes the
  data you pass in; it does not fetch missing history.

## Exporter

Signature:

```python
Exporter(data: Any)
```

Purpose: export models and lists to lightweight formats.

Methods:

| Method | Return type | Purpose |
| --- | --- | --- |
| `json(*, indent=2)` | `str` | JSON string using model conversion. |
| `csv(*, columns=None)` | `str` | CSV text. |
| `markdown(*, columns=None)` | `str` | Markdown table. |
| `html(*, columns=None)` | `str` | HTML table. |
| `xlsx(path, *, sheet_name="data", columns=None)` | `Path` | Write XLSX workbook. |

Minimal example:

```python
from erlc_api.export import Exporter

players = await api.players()
csv_text = Exporter(players).csv(columns=["name", "user_id", "team"])
md_table = Exporter(players).markdown()
```

HTML example:

```python
html_table = Exporter(await api.vehicles()).html(columns=["name", "owner", "plate"])
```

Optional extra:

```bash
pip install "erlc-api.py[export]"
```

Required only for:

```python
path = Exporter(await api.players()).xlsx("players.xlsx", sheet_name="players")
```

Important options:

- `columns=` controls output order and included fields for table formats.
- Nested dicts/lists are JSON encoded inside cells.
- `raw` and `extra` are omitted from flattened table rows.

Common mistakes:

- Expecting `.xlsx()` to return bytes. It writes the workbook and returns a `Path`.
- Expecting `html()` to create a full web page. It returns a table fragment.

## Practical Dashboard Example

Async:

```python
from erlc_api.analytics import Analyzer
from erlc_api.format import Formatter

bundle = await api.server(all=True)
summary = Analyzer(bundle).dashboard()
line = Formatter().server(bundle)

print(line, summary.players_by_team)
```

Sync:

```python
from erlc_api import ERLC
from erlc_api.analytics import Analyzer
from erlc_api.export import Exporter

with ERLC("server-key") as api:
    bundle = api.server(all=True)
    print(Analyzer(bundle).dashboard())
    print(Exporter(bundle.players or []).csv())
```

## Related Pages

- [Earlier in the guide: Workflow Utilities Reference](./Workflow-Utilities-Reference.md)
- [Next in the guide: Moderation Helpers](./Moderation-Helpers.md)

---

[Previous Page: Workflow Utilities Reference](./Workflow-Utilities-Reference.md) | [Next Page: Moderation Helpers](./Moderation-Helpers.md)
