# erlc-api Wiki

`erlc-api` v2.0 is a lightweight sync and async wrapper for the ER:LC PRC API.
It uses flat clients, typed dataclasses by default, raw JSON escape hatches,
flexible commands, and explicit utility modules.

## Start Here

1. [Getting Started](./Getting-Started.md)
2. [Clients and Authentication](./Clients-and-Authentication.md)
3. [Endpoint Reference](./Endpoint-Reference.md)
4. [Commands Reference](./Commands-Reference.md)
5. [Utilities Reference](./Utilities-Reference.md)

## API Reference

- [Clients and Authentication](./Clients-and-Authentication.md): constructors,
  lifecycle, headers, `server_key=`, `global_key=`, validation, and raw requests.
- [Endpoint Reference](./Endpoint-Reference.md): every flat endpoint method,
  PRC path, return type, options, examples, and common mistakes.
- [Models Reference](./Models-Reference.md): dataclass fields, helpers, `.raw`,
  `.extra`, `.to_dict()`, and player identifier parsing.
- [Commands Reference](./Commands-Reference.md): plain strings, `cmd`, dry-run,
  normalization, validation, and command error behavior.
- [Errors and Rate Limits](./Errors-and-Rate-Limits.md): exception mapping,
  `RateLimitError`, retry behavior, and validation statuses.

## Utilities

Utilities are explicit imports, for example:

```python
from erlc_api.find import Finder
from erlc_api.wait import AsyncWaiter
from erlc_api.export import Exporter
```

See:

- [Utilities Reference](./Utilities-Reference.md)
- [Waiters and Watchers](./Waiters-and-Watchers.md)
- [Formatting, Analytics, and Export](./Formatting-Analytics-and-Export.md)
- [Moderation Helpers](./Moderation-Helpers.md)

## Operations

- [Webhooks Reference](./Webhooks-Reference.md)
- [Quickstart: Discord.py](./Quickstart-Discord.py.md)
- [Quickstart: Web Backend](./Quickstart-Web-Backend.md)

## Migration

Start with [Migration to v2](./Migration-to-v2.md) if you have older code.

---

[Getting Started](./Getting-Started.md) →
