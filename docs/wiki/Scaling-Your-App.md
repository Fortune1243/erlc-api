# Scaling Your App

This page maps PRC large-app guidance to `erlc-api.py` features. It is not a
replacement for PRC's official requirements.

## When To Think About Scaling

Consider scaling patterns when your app:

- serves multiple private servers;
- runs many Discord commands or dashboards;
- polls frequently for watchers;
- uses a PRC global key;
- runs across multiple processes, containers, or bot shards.

## Wrapper Features

| Need | Feature |
| --- | --- |
| Avoid preventable rate limits | `rate_limited=True` on clients by default. |
| Inspect rate-limit state | `api.rate_limits.to_dict()`. |
| Reduce repeated reads | `AsyncCachedClient` / `CachedClient`. |
| Bound multi-server fanout | `AsyncMultiServer(..., concurrency=...)`. |
| Audit moderation flows | `AuditLog` and `CommandPolicy`. |
| Diagnose failures | `diagnose_error(...)` and `error_codes`. |

## Headers To Monitor

- `X-RateLimit-Bucket`
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`
- `Retry-After`

## Global Keys

Use `global_key=` only when PRC grants your application an Authorization key:

```python
api = AsyncERLC("server-key", global_key="global-key")
```

Global-key requests are tracked separately from server-key-only requests by the
dynamic limiter.

## Multi-process Limits

The built-in limiter is process-local. If multiple containers share keys, use an
external queue, cache, or distributed rate limiter in your application.

## Common Mistakes

- Running one watcher per Discord guild at one-second intervals.
- Treating `retry_429=True` as a full retry strategy.
- Caching command execution. Cache helpers intentionally skip commands.
- Sharing keys across workers without external coordination.

---

[Previous Page: Rate Limits, Retries, and Reliability](./Rate-Limits-Retries-and-Reliability.md) | [Next Page: Errors and Rate Limits](./Errors-and-Rate-Limits.md)
