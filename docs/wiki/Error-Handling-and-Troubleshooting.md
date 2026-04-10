# Error Handling and Troubleshooting

Treat API/transport failures as normal runtime states and branch on structured exception types.

## Exception map

| Exception | Meaning | Typical action |
|---|---|---|
| `AuthError` | Invalid/unauthorized key | Re-check key and access |
| `PermissionDeniedError` | Authenticated but insufficient permission | Adjust role/scope |
| `RateLimitError` | Bucket-limited request | Retry using hints/backoff |
| `CircuitOpenError` | Circuit breaker open for bucket | Delay and retry later |
| `NetworkError` | Transport failure | Retry idempotent flows |
| `PlayerNotFoundError` | Target player not present | Re-resolve target |
| `ServerEmptyError` | No data/players for request | Handle empty-state UI/logic |
| `InvalidCommandError` | Command syntax rejected | Validate/build command |
| `RobloxCommunicationError` | Upstream Roblox communication failure | Retry/degrade gracefully |
| `APIError` | Other non-success API status | Log + status-based handling |
| `ModelDecodeError` | Typed top-level payload mismatch | Fallback to raw/validated path |

## Recommended boundary pattern

```python
from erlc_api import (
    APIError,
    AuthError,
    CircuitOpenError,
    ModelDecodeError,
    NetworkError,
    RateLimitError,
)

try:
    data = await client.v2.server_default_typed(ctx)
except AuthError:
    ...
except (RateLimitError, CircuitOpenError):
    ...
except NetworkError:
    ...
except ModelDecodeError:
    data = await client.v2.server_default(ctx)
except APIError:
    ...
```

## Common issues

1. `RuntimeError: HTTP client not started`
   - Use `await client.start()` or `async with ERLCClient() as client`.
2. Repeated auth failures
   - Check `await client.validate_key(ctx)`.
3. Unexpected command result ambiguity
   - Use `command_with_tracking(...)` and inspect `inferred_success` + correlation flags.
4. Cache confusion during testing
   - Use `await client.invalidate(ctx)` or `await client.clear_cache()`.

## Next Steps

- Return to onboarding: [Getting-Started.md](./Getting-Started.md)
- Reliability details: [Rate-Limits-Retries-and-Reliability.md](./Rate-Limits-Retries-and-Reliability.md)
