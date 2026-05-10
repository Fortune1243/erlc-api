# Comparison and Why erlc-api.py

`erlc-api.py` v2 focuses on the smallest useful wrapper surface: flat clients,
typed responses, flexible commands, lazy utilities, and framework-neutral
webhook helpers.

The root [comparison.md](../../comparison.md) contains a compact package
comparison table. In short: `erlc-api.py` is flat, sync+async, utility-rich, and
typed by default; `prc.api-py` is async-first with strong model/cache ideas that
inspired the v2.4 vehicle catalog and request-safety polish.

## Design Goals

| Goal | What it means |
| --- | --- |
| Lightweight base install | Only `httpx` is required at runtime. |
| v2-first API | Prefer PRC v2 endpoints where available. |
| Flat client surface | Use `api.players()` instead of grouped `client.v2.server.players()`. |
| Typed by default | Return dataclasses with `.raw`, `.extra`, and `.to_dict()`. |
| Escape hatches | Keep `raw=True` and `request()` for exact payloads or new endpoints. |
| Explicit utilities | Import helpers only when needed. |

## What Was Removed

The old heavy ops stack is intentionally not part of the public v2 surface:

- cache and Redis backends;
- metrics sinks;
- request replay buffers;
- tracing and structured logging integrations;
- circuit breakers;
- request coalescing;
- public `client.v1` and `client.v2` context objects.

These features are better owned by the application or hosting platform.

## What Was Kept

The wrapper keeps user-facing helpers that make scripts and bots easier:

- sync and async clients;
- flexible command composition;
- find, filter, sort, group, diff, wait, watch, format, analytics, export, and
  moderation utilities;
- webhook signature verification and event routing;
- custom command routing for PRC webhook messages starting with `;`;
- ops utilities for snapshots, audit records, idempotency, and polling guidance.
- v2.4 workflow helpers for vehicle catalogs, permission levels, wanted stars,
  and emergency calls.

## When This Wrapper Fits

Use this wrapper when you want:

- a small dependency footprint;
- plain Python objects instead of framework lock-in;
- both sync scripts and async bots;
- documented escape hatches for new PRC behavior.

Use direct `httpx` calls when you need:

- total control over every request;
- experimental PRC behavior before wrapper models exist;
- a custom transport stack with organization-specific middleware.

## Common Mistakes

- Expecting v1-style grouped clients in v2 code.
- Treating utility modules as part of top-level import cost.
- Looking for Redis/cache behavior that was intentionally removed.
- Assuming lightweight means no helpers; v2 keeps pure user-facing utilities.

## Related Pages

- [Migration to v2](./Migration-to-v2.md)
- [Installation and Extras](./Installation-and-Extras.md)
- [Ops Utilities Reference](./Ops-Utilities-Reference.md)

---

[Previous Page: Migration to v2](./Migration-to-v2.md) | [Next Page: Home](./Home.md)
