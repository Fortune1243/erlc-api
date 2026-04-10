# Rate Limits, Retries, and Reliability

This wrapper is intentionally engineered for long-running bot and backend workloads.

## Reliability behavior

- Tracks route buckets from ER:LC rate-limit headers.
- Isolates limiter state by server key + bucket.
- Retries safe/idempotent requests on transient failures.
- Retries `429` responses using server retry hints when available.
- Does not automatically replay non-idempotent command requests.

## Why this matters in production

- Fewer burst failures when many guilds/servers share one process.
- Lower risk of command duplication on unstable networks.
- Predictable retry behavior for operational dashboards and automations.

## Polling guidance

Use consumer-managed async iterators and control interval based on your own workload constraints:

```python
from erlc_api.utils.polling import poll_server_default

async for snapshot in poll_server_default(client, ctx, interval_s=5.0):
    if snapshot.diff and snapshot.diff.players:
        print("joined:", len(snapshot.diff.players.joined))
```

## Operational recommendations

- Keep `interval_s` conservative in shared deployments.
- Catch `RateLimitError` and `NetworkError` at integration boundaries.
- Use one `ERLCClient` process-wide and per-server `ctx(...)` objects.

## Next Steps

- Implement defensive exception handling in [Error-Handling-and-Troubleshooting.md](./Error-Handling-and-Troubleshooting.md)
- Review real endpoint examples in [Endpoint-Usage-Cookbook.md](./Endpoint-Usage-Cookbook.md)
