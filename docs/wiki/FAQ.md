# FAQ

## Is this official?

No. This is an independent community wrapper for the ER:LC PRC API.

## Is v2 breaking?

Yes. The public API is now `AsyncERLC` and `ERLC` with flat methods.

## What is the package name?

Install with `erlc-api.py` and import with `erlc_api`:

```bash
pip install erlc-api.py
```

```python
from erlc_api import AsyncERLC
```

## How do I use multiple servers?

Set a default server key on the client and override with `server_key=` when
needed.

## Can I get raw JSON?

Yes. Pass `raw=True` to endpoint methods.

## Is `:log` blocked?

No. v2 only performs minimal command syntax validation.

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

## Does the wrapper include a Discord bot framework?

No. It includes framework-neutral helpers and Discord-safe formatting utilities.
You bring your own bot framework and close over `AsyncERLC` where needed.

## How should I verify webhooks?

Use `assert_valid_event_webhook_signature()` with the raw request body before
trusting the decoded JSON payload.

## Related Pages

- [Getting Started](./Getting-Started.md)
- [Security and Secrets](./Security-and-Secrets.md)
- [Webhooks Reference](./Webhooks-Reference.md)

---

[Previous Page: Quickstart: Discord.py](./Quickstart-Discord.py.md) | [Next Page: Clients and Authentication](./Clients-and-Authentication.md)
