# Waiters and Watchers

Waiters and watchers are the utility layer that calls the API for you. They are
explicit modules so the base package stays small.

Async imports:

```python
from erlc_api.wait import AsyncWaiter
from erlc_api.watch import AsyncWatcher
```

Sync imports:

```python
from erlc_api.wait import Waiter
from erlc_api.watch import Watcher
```

## Safe Polling

The default interval is `2.0` seconds. Pass a larger interval for low-traffic
jobs or when you are close to rate limits.

Common mistakes:

- Setting very small intervals for busy servers.
- Forgetting that waiters use repeated API calls.
- Expecting waiters to bypass PRC rate limits. They do not.

## AsyncWaiter

Signature:

```python
AsyncWaiter(api: Any, *, server_key: str | None = None, interval_s: float = 2.0)
```

Purpose: await common server conditions.

Methods:

| Method | Return type | Purpose |
| --- | --- | --- |
| `player_join(query, *, timeout_s=60.0, interval_s=None)` | `Player` | Wait until a matching new player appears. |
| `player_leave(query, *, timeout_s=60.0, interval_s=None)` | `Player | None` | Wait until a matching player leaves. |
| `staff_appears(query, *, timeout_s=60.0, interval_s=None)` | `StaffMember` | Wait until a staff member appears. |
| `command_log(command_prefix=None, contains=None, player=None, timeout_s=60.0, interval_s=None)` | `CommandLogEntry` | Wait for a matching command log. |
| `queue_change(*, timeout_s=60.0, interval_s=None)` | `list[int]` | Wait for queue IDs to change. |
| `player_count(predicate=None, *, equals=None, at_least=None, at_most=None, timeout_s=60.0, interval_s=None)` | `int` | Wait until player count satisfies a condition. |

Minimal example:

```python
from erlc_api import AsyncERLC
from erlc_api.wait import AsyncWaiter

async with AsyncERLC("server-key") as api:
    waiter = AsyncWaiter(api, interval_s=5)
    joined = await waiter.player_join("Avi", timeout_s=120)
    print(joined.name)
```

Important options:

- `server_key=` pins the waiter to one server key.
- Per-call `interval_s=` overrides the default interval.
- `timeout_s` must be greater than zero.

Common mistakes:

- Waiting for a player join when the player was already present before the wait started. `player_join` tracks the initial snapshot and waits for a new match.

## Waiter

Signature:

```python
Waiter(api: Any, *, server_key: str | None = None, interval_s: float = 2.0)
```

Purpose: sync version of `AsyncWaiter`.

Methods:

| Method | Return type | Purpose |
| --- | --- | --- |
| `player_join(query, *, timeout_s=60.0, interval_s=None)` | `Player` | Wait until a matching new player appears. |
| `player_leave(query, *, timeout_s=60.0, interval_s=None)` | `Player | None` | Wait until a matching player leaves. |
| `staff_appears(query, *, timeout_s=60.0, interval_s=None)` | `StaffMember` | Wait until a staff member appears. |
| `command_log(command_prefix=None, contains=None, player=None, timeout_s=60.0, interval_s=None)` | `CommandLogEntry` | Wait for a matching command log. |
| `queue_change(*, timeout_s=60.0, interval_s=None)` | `list[int]` | Wait for queue IDs to change. |

Minimal example:

```python
from erlc_api import ERLC
from erlc_api.wait import Waiter

with ERLC("server-key") as api:
    current_queue = Waiter(api, interval_s=5).queue_change(timeout_s=300)
    print(current_queue)
```

Common mistakes:

- Using sync `Waiter` inside async frameworks. Use `AsyncWaiter`.

## WatchEvent

Signature:

```python
WatchEvent(type: str, item: Any = None, diff: BundleDiff | None = None, snapshot: Any = None)
```

Purpose: event object yielded by watchers.

Fields:

| Field | Meaning |
| --- | --- |
| `type` | Event type string. |
| `item` | Added/removed item when the event represents one item. |
| `diff` | Full `BundleDiff` for the snapshot comparison. |
| `snapshot` | Current server bundle. |

Event types:

| Event type | Emitted when |
| --- | --- |
| `snapshot` | Every poll comparison. |
| `player_join` | A player appears. |
| `player_leave` | A player disappears. |
| `staff_join` | A staff member appears. |
| `staff_leave` | A staff member disappears. |
| `queue_change` | Queue IDs are added or removed. |
| `command_executed` | A new command log appears. |
| `mod_call` | A new mod call appears. |
| `emergency_call` | A new emergency call appears. |
| `vehicle_change` | A vehicle appears or disappears. |

## AsyncWatcher

Signature:

```python
AsyncWatcher(api: Any, *, server_key: str | None = None, interval_s: float = 2.0)
```

Purpose: poll `api.server(all=True)` and emit stream events from diffs.

Methods:

| Method | Return type | Purpose |
| --- | --- | --- |
| `on(event_type, callback)` | `AsyncWatcher` | Register sync or async callback. |
| `events(*, limit=None)` | `AsyncIterator[WatchEvent]` | Yield events until limit or forever. |

Minimal example:

```python
from erlc_api.watch import AsyncWatcher

watcher = AsyncWatcher(api, interval_s=5)


async def joined(event):
    print("joined", event.item.name)


watcher.on("player_join", joined)

async for event in watcher.events(limit=10):
    print(event.type)
```

Important options:

- Register `event_type="*"` to receive every event in one callback.
- `limit=None` runs forever.

Common mistakes:

- Expecting the first snapshot to emit all existing players. Watchers compare
  the first snapshot to later snapshots.

## Watcher

Signature:

```python
Watcher(api: Any, *, server_key: str | None = None, interval_s: float = 2.0)
```

Purpose: sync version of `AsyncWatcher`.

Methods:

| Method | Return type | Purpose |
| --- | --- | --- |
| `on(event_type, callback)` | `Watcher` | Register sync callback. |
| `events(*, limit=None)` | `Iterator[WatchEvent]` | Yield events until limit or forever. |

Minimal example:

```python
from erlc_api.watch import Watcher

watcher = Watcher(api, interval_s=10)
watcher.on("*", lambda event: print(event.type))

for event in watcher.events(limit=5):
    print(event.snapshot.name)
```

Common mistakes:

- Registering async callbacks on sync `Watcher`. Use `AsyncWatcher` for async callbacks.

## Scheduling Extra

`erlc-api[scheduling]` installs `apscheduler` for apps that want to wrap watcher
or polling calls in a scheduler. The core watcher classes do not require it.
