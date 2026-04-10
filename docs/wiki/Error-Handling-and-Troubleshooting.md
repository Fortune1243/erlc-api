# Error Handling and Troubleshooting

Treat external API failures as normal runtime states. `erlc-api` provides explicit error types so recovery logic is clean.

## Exception map

| Exception | Meaning | Typical action |
|---|---|---|
| `AuthError` | Invalid/unauthorized key or insufficient permission | Verify key, key scope, and target server |
| `RateLimitError` | Rate limited response | Back off and retry after suggested delay |
| `NetworkError` | Transport-level failure | Retry idempotent flows and inspect network path |
| `APIError` | Other non-success API status | Log status/body excerpt and handle by status |
| `NotFoundError` | Requested API path/resource not found | Verify endpoint and API support |
| `ModelDecodeError` | Typed top-level payload shape mismatch | Fallback to raw mode + log payload shape |

## Recommended boundary pattern

```python
from erlc_api import APIError, AuthError, ModelDecodeError, NetworkError, RateLimitError

try:
    data = await client.v2.server_default_typed(ctx)
except AuthError:
    # mark configuration invalid
    ...
except RateLimitError as exc:
    # schedule retry based on retry hints
    ...
except NetworkError:
    # retry with backoff in caller
    ...
except ModelDecodeError:
    # fallback to raw endpoint if needed
    data = await client.v2.server_default(ctx)
except APIError as exc:
    # generic structured handling
    ...
```

## Common issues

1. `RuntimeError: HTTP client not started`
   - Fix: call `await client.start()` before requests.
2. Repeated auth failures
   - Fix: validate keys with `await client.validate_key(ctx)` during setup.
3. Unexpected typed decoding errors
   - Fix: log payload shape, switch to raw temporarily, update parser assumptions.

## Next Steps

- Return to onboarding via [Getting-Started.md](./Getting-Started.md)
- Check frequent questions in [FAQ.md](./FAQ.md)
