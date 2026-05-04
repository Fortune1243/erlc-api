# Why erlc-api.py

erlc-api.py is the only ER:LC Python wrapper with both a sync and async client,
a command safety policy system, and 30+ production utility modules covering
everything from analytics and export to moderation and rules engines. It is built
for bots and dashboards that have to be correct and maintainable — not just
functional.

## What sets erlc-api.py apart

**Both sync and async, same API surface.**
`erlcPY` is sync-only. `prc.api-py` is async-only. `erlc-api.py` ships `ERLC`
and `AsyncERLC` with identical method names, so you can write sync scripts, async
Discord bots, and FastAPI backends without switching libraries or relearning an
API.

**The deepest exception taxonomy.**
14 typed exception classes — `RateLimitError`, `AuthError`,
`RestrictedCommandError`, `ProhibitedMessageError`, `ServerOfflineError`,
`RobloxCommunicationError`, and more — so you catch exactly what went wrong
instead of pattern-matching error strings or swallowing a generic `Exception`.

**Command safety by design.**
`CommandPolicy` is the only command safety system among ER:LC Python wrappers.
Define an allowlist of permitted commands, a max length cap, and dry-run before
any HTTP is sent. Discord bots and web routes should never trust input blindly;
`CommandPolicy` gives you the enforcement layer.

**Frozen dataclasses as default responses.**
Typed, immutable, hashable, and thread-safe by default. Every model keeps its
original payload in `.raw`, unknown fields in `.extra`, and converts cleanly with
`.to_dict()`. No silent attribute surprises, no mutable shared state bugs.

**Per-request multi-server key.**
One client instance, any number of servers — pass `server_key=` on any method
call. No separate client per server, no credential juggling across instances.

**Explicit, transparent caching.**
`CachedClient` / `AsyncCachedClient` cache read endpoints with a configurable TTL
and expose cache stats. No hidden background expiry — you control when the cache
is consulted and when it is bypassed.

**30+ utility modules, lazy-loaded.**
`Finder`, `Filter`, `Analyzer`, `Exporter`, `RuleEngine`, `AsyncWatcher`,
`VehicleTools`, `EmergencyCallTools`, `Moderator`, `DiscordFormatter`, and more.
None of them load unless you import them. The core client stays lightweight
regardless of how many extras are installed.

**The only ER:LC library with a full documentation wiki.**
30+ dedicated pages covering quickstarts, cookbook examples, migration guides,
security practices, scaling patterns, and every utility module in depth. No other
wrapper comes close.

## Feature comparison

| Feature | erlc-api.py | erlcPY | prc.api-py | ERLC.py |
| --- | --- | --- | --- | --- |
| Sync client | Yes, `ERLC` | Yes | No | Yes |
| Async client | Yes, `AsyncERLC` | No | Yes | Partial |
| Both sync + async | **Yes** | No | No | No |
| v2-first endpoint coverage | Yes | Limited | Yes | Limited |
| Raw response access | `raw=True` | Yes | Yes | Yes |
| Typed response models | **Frozen dataclasses** | Minimal | Classes | Minimal |
| Exception taxonomy | **14+ typed classes** | Basic | Typed | Basic |
| Command safety policy | **Yes, `CommandPolicy`** | No | No | No |
| Lazy utility modules | **30+ modules** | No | Some helpers | No |
| Explicit read caching | `CachedClient` / `AsyncCachedClient` | No | Built in | No |
| Per-request server key | **Yes, `server_key=`** | No | Server objects | No |
| Multi-server aggregation | `AsyncMultiServer` / `MultiServer` | No | No | No |
| Analytics / dashboard summaries | **Yes, `Analyzer`** | No | No | No |
| Rules / alert engine | **Yes, `RuleEngine`** | No | No | No |
| Export (CSV, JSON, HTML, XLSX) | **Yes, `Exporter`** | No | No | No |
| Discord embed helpers | **Yes, dependency-free** | No | No | No |
| Moderation helpers | **Yes, `Moderator`** | No | No | No |
| Event webhook helpers | Yes | No | Yes | Unknown |
| Custom command router | Yes | No | Command parser | No |
| Vehicle catalog / tools | Yes, v2.4+ | No | Yes | No |
| WantedStars support | Yes | Unknown | Yes | Unknown |
| Emergency call support | Yes | Unknown | Yes | Unknown |
| Dynamic rate limiting | **Default-on, adaptive** | Basic | Yes | Basic |
| Key fingerprint / safe logging | **Yes** | No | No | No |
| Documentation depth | **30+ wiki pages** | Basic README | README + docs | Basic |
| Python floor | 3.11+ | Varies | 3.8+ | Varies |
| License | Custom attribution | Varies | MIT | Varies |

## When to choose erlc-api.py

- **Discord bot** — you need command safety, rate-limit discipline, moderation
  helpers, and dependency-free Discord embed builders out of the box.
- **Web dashboard** — analytics summaries, flexible export (CSV, JSON, HTML,
  XLSX), and structured typed data that serializes cleanly.
- **Mixed sync + async codebase** — one library, one API surface, no client
  swap when you move from a sync script to an async bot.
- **Multi-server operator** — read and aggregate across named servers with
  bounded concurrency from a single client instance.
- **Production reliability** — fine-grained exception handling, adaptive rate
  limiting, explicit caching, and a rules/alert engine that tells you when
  something in-game needs attention.
- **Long-term maintainability** — frozen typed responses, 14 distinct exception
  classes, and 30+ wiki pages mean less guessing, less debugging, and less
  onboarding friction as your project grows.
