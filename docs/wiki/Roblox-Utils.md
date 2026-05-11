# Roblox Utils

`erlc_api.roblox` is a lazy utility module for resolving Roblox user IDs,
usernames, and public profile fields without turning `erlc-api.py` into a full
Roblox SDK.

It uses Roblox public user endpoints and does not need cookies, Roblox API keys,
or PRC server keys.

## Install

Roblox lookup works with the base `httpx` dependency. The `roblox` extra is
available for explicit installs:

```bash
pip install "erlc-api.py[roblox]"
```

## Import

```python
from erlc_api.roblox import AsyncRobloxClient, RobloxClient
```

Do not import these classes from top-level `erlc_api`; utility imports stay
explicit.

## Async Lookup

```python
from erlc_api.roblox import AsyncRobloxClient

async with AsyncRobloxClient() as roblox:
    user = await roblox.user(1)
    if user:
        print(user.name, user.display_name, user.has_verified_badge)

    by_name = await roblox.user_by_username("Roblox")
    print(by_name.user_id if by_name else "not found")
```

`user(id)` fetches detailed public profile data. Use `users(ids)` when you need
a batch lookup:

```python
users = await roblox.users([1, 156, 999999999])
for user_id, user in users.items():
    print(user_id, user.name)
```

Batch methods return dictionaries and omit misses.

## Sync Lookup

```python
from erlc_api.roblox import RobloxClient

with RobloxClient() as roblox:
    print(roblox.username(1))
    users = roblox.users_by_username(["Roblox", "builderman"])
```

## Model

`RobloxUser` includes:

| Field | Meaning |
| --- | --- |
| `user_id` | Roblox user ID. |
| `name` | Current Roblox username. |
| `display_name` | Current display name. |
| `has_verified_badge` | Whether Roblox reports a verified badge. |
| `requested_username` | Input username returned by username lookups. |
| `description` | Public profile description from detailed lookup. |
| `created_at` | Raw Roblox creation timestamp string. |
| `is_banned` | Public banned flag from detailed lookup. |
| `external_app_display_name` | Roblox external app display name when present. |
| `raw` / `extra` | Original payload and unrecognized fields. |

Use `.to_dict()` for JSON-safe model-shaped output. Pass `raw=True` when you
want the exact Roblox payload for each returned user.

## Cache Behavior

Successful lookups are cached in memory for one hour by default:

```python
roblox = RobloxClient(ttl_s=600)
user = roblox.user(1)
again = roblox.user(1)  # served from cache
print(roblox.cache_stats().to_dict())
roblox.clear_cache()
```

Misses are not cached. If a username or ID does not resolve, a later call will
try Roblox again.

## Banned Users

Username lookup defaults to `exclude_banned_users=False` so moderation and log
tools can resolve as much historical data as Roblox still exposes:

```python
user = await roblox.user_by_username("SomeName", exclude_banned_users=True)
```

## Errors

Missing or invalid users return `None` for single lookups and are omitted from
batch mappings. Roblox outages, malformed responses, and rate limits raise
module-local exceptions:

```python
from erlc_api.roblox import RobloxAPIError, RobloxNetworkError, RobloxRateLimitError

try:
    user = await roblox.user(1)
except RobloxRateLimitError as exc:
    print(exc.retry_after_s)
except RobloxNetworkError:
    print("Roblox network request failed")
except RobloxAPIError:
    print("Roblox returned an API error")
```

## Common Mistakes

- Treating `RobloxClient` as a PRC client. It does not call ER:LC endpoints and
  does not use server keys.
- Using sync lookup methods inside async Discord bot handlers. Use
  `AsyncRobloxClient` in async apps.
- Assuming `raw=True` returns a top-level batch response. Batch methods still
  return dictionaries keyed by requested ID or username.

## Related Pages

- [Utilities Reference](./Utilities-Reference.md)
- [Workflow Utilities Reference](./Workflow-Utilities-Reference.md)
- [Security and Secrets](./Security-and-Secrets.md)

---

[Previous Page: Utilities Reference](./Utilities-Reference.md) | [Next Page: Vehicle Tools](./Vehicle-Tools.md)
