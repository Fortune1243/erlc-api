# Rate Limits, Retries, and Reliability

This wrapper is built for long-running bot/backend workloads.

## Implemented reliability behavior

- Tracks route buckets from ER:LC `X-RateLimit-*` headers.
- Isolates limiter state by server key + bucket.
- Uses reset-aware pre-acquire before sending requests.
- Supports optional per-bucket circuit breaker with half-open probing.
- Retries idempotent requests for configured categories:
  - `429` (retry hints / reset timestamp / backoff)
  - `5xx`
  - network errors
- Uses exponential backoff with jitter.
- Optionally coalesces duplicate in-flight idempotent GET requests.
- Never auto-replays non-idempotent command requests.

## Cache behavior

- Optional TTL cache for idempotent GET requests.
- Default endpoint TTL map provided in config.
- Manual invalidation via `client.invalidate(...)`.
- Runtime cache stats via `client.cache_stats()`.

## Key config knobs (`ClientConfig`)

- `max_retries`, `retry_429`, `retry_5xx`, `retry_network`
- `backoff_base_s`, `backoff_cap_s`, `backoff_jitter_s`
- `request_coalescing`
- `cache_enabled`, `cache_ttl_by_path`, `cache_backend`
- `circuit_breaker_enabled`, `circuit_failure_threshold`, `circuit_open_s`
- `debug_dump`, `request_replay_size`

## Metrics hook notes

When `metrics_sink` is configured:

- request/rate-limit/cache metrics are emitted from HTTP transport
- command metrics are emitted from v1 command paths:
  - `command(...)`
  - `send_command(...)`
  - `command_with_tracking(...)` (single final metric per tracked call)

## Operational guidance

- Use one shared `ERLCClient` per process.
- Create per-server contexts with `client.ctx(...)`.
- Keep polling intervals conservative in multi-guild/multi-server workloads.
- Inspect redacted replay entries with `client.request_replay(...)` during incident response.

## Next Steps

- Exception handling strategy: [Error-Handling-and-Troubleshooting.md](./Error-Handling-and-Troubleshooting.md)
- Practical endpoint patterns: [Endpoint-Usage-Cookbook.md](./Endpoint-Usage-Cookbook.md)
