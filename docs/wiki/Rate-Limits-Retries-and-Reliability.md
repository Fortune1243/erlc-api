# Rate Limits, Retries, and Reliability

v2.0 keeps rate-limit behavior intentionally small.

- Every request sends `Server-Key`.
- `global_key=` sends `Authorization`.
- `429` responses raise `RateLimitError`.
- `RateLimitError` exposes `retry_after`, `reset_epoch_s`, `bucket`, and `error_code` when available.
- By default the wrapper sleeps once and retries once on `429`.
- Pass `retry_429=False` to handle rate limits manually.

The v1 ops stack was removed: no cache, Redis backend, metrics sink, replay buffer, tracing, circuit breaker, or request coalescing.


---

← [Errors and Rate Limits](./Errors-and-Rate-Limits.md) | [Error Handling and Troubleshooting](./Error-Handling-and-Troubleshooting.md) →
