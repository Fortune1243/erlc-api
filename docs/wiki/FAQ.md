# FAQ

## Is this official?

No. This is an independent community wrapper for the ER:LC PRC API.

## Is v3 breaking?

Yes. v3 keeps the v2 feature set but adds simpler aliases and helpers. Use
`Client` / `AsyncClient`, `from_env()`, `bundle()`, `logs(...)`, and
`preview_command(...)` for the easiest path.

## What is the package name?

Install with `erlc-api.py` and import with `erlc_api`:

```bash
pip install erlc-api.py
```

```python
from erlc_api import AsyncClient
```

## How do I use multiple servers?

Set a default server key on the client and override with `server_key=` when
needed.

## Can I get raw JSON?

Yes. Pass `raw=True` to endpoint methods.

## Is `:log` blocked?

No. v3 only performs minimal command syntax validation unless you pass
`policy=` to `command(...)`.

## Where did cache, metrics, replay, and Redis go?

They were removed to keep the wrapper lightweight. Use your application,
hosting platform, or own ops stack for heavyweight reliability features.

## Are utilities imported by default?

No. `import erlc_api` imports clients, models, errors, and command helpers.
Utility modules are explicit imports, for example:

```python
from erlc_api.find import Finder
from erlc_api.snapshot import SnapshotStore
```

## Can I resolve Roblox user IDs and usernames?

Yes. Use the lazy Roblox utility module:

```python
from erlc_api.roblox import AsyncRobloxClient

async with AsyncRobloxClient() as roblox:
    user = await roblox.user(1)
```

Missing users return `None`; Roblox outages and rate limits raise
`erlc_api.roblox` exceptions.

## Does the wrapper include a Discord bot framework?

No. It includes framework-neutral helpers and Discord-safe formatting utilities.
You bring your own bot framework and close over `AsyncClient` where needed.

## How should I verify webhooks?

Use `assert_valid_event_webhook_signature()` with the raw request body before
trusting the decoded JSON payload.

## Related Pages

- [Clients and Authentication](./Clients-and-Authentication.md)
- [Security and Secrets](./Security-and-Secrets.md)
- [Webhooks Reference](./Webhooks-Reference.md)

---

[Previous Page: Installation and Extras](./Installation-and-Extras.md) | [Next Page: Clients and Authentication](./Clients-and-Authentication.md)
