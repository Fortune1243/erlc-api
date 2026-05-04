# Testing and Mocking

This page shows how to test code built on `erlc-api.py` without calling the live
PRC API.

## Fake Async Client

Use small fake clients for application tests:

```python
class FakeAPI:
    async def players(self, **_kwargs):
        return []

    async def command(self, command, **_kwargs):
        return {"command": command, "success": True}
```

Pass the fake into your service, command handler, or watcher wrapper.

## Fake Sync Client

```python
class FakeSyncAPI:
    def players(self, **_kwargs):
        return []
```

This keeps CLI and script tests fast and deterministic.

## Fixture-based Raw Payloads

Use `raw=True` output or official examples as fixtures:

```python
payload = [{"Player": "Avi:123", "Team": "Police"}]
```

Then decode through public model functions or client-facing code paths. Prefer
public APIs where possible; raw fixture tests should catch payload drift without
locking every application test to PRC JSON.

## Command Dry-runs

Use `dry_run=True` to test command composition without sending HTTP:

```python
from erlc_api import cmd

result = await api.command(cmd.pm("Player", "hello"), dry_run=True)
assert result.raw["command"] == ":pm Player hello"
```

## Webhook Payload Tests

Test decoding separately from signature verification:

```python
from erlc_api.webhooks import decode_event_webhook_payload

event = decode_event_webhook_payload({"Message": ";ping"})
assert event.command.command_name == "ping"
```

For signature verification tests, keep raw bytes and headers together. Do not
verify a reserialized body.

## Waiter And Watcher Tests

Use fake clients that return different snapshots over time:

```python
class ChangingAPI:
    def __init__(self):
        self.calls = 0

    async def players(self, **_kwargs):
        self.calls += 1
        return [] if self.calls == 1 else [{"Player": "Avi:123"}]
```

Keep polling intervals tiny in tests and timeouts short.

## Optional Dependency Tests

For extras, assert helpful errors when dependencies are missing. Do not import
optional libraries at module import time in utility modules.

## Rate Limiter Tests

Use injected clocks and sleep functions to avoid real delays:

```python
from erlc_api.ratelimit import RateLimiter

now = 100.0
sleeps = []

limiter = RateLimiter(now=lambda: now, sleep=sleeps.append)
limiter.after_response(
    "GET",
    "/v2/server",
    {"X-RateLimit-Bucket": "global", "X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "105"},
)

assert limiter.before_request("GET", "/v2/server") == 5.0
```

For client integration tests, pass fake transports. Rate limiting is enabled by
default, so pass `rate_limited=False` only when a test specifically needs the
old no-limiter behavior.

## Error Code Tests

```python
from erlc_api.error_codes import explain_error_code

info = explain_error_code(4001)
assert info.retryable is True
```

Also assert that top-level `import erlc_api` does not import
`erlc_api.error_codes` or `erlc_api.ratelimit`.

## Workflow Utility Tests

The 2.3 workflow utilities are easiest to test with fake clients and already
decoded models:

```python
from erlc_api.bundle import AsyncBundle
from erlc_api.status import StatusBuilder
from erlc_api.cache import AsyncCachedClient

bundle = await AsyncBundle(fake_api).dashboard()
status = StatusBuilder(bundle).build()
cached = AsyncCachedClient(fake_api, ttl_s=5)
```

Recommended scenarios:

- location geometry and map URL helpers with fixed coordinates;
- missing Pillow errors for `MapRenderer`;
- bundle preset expansion and invalid include names;
- rule matches and callbacks without command side effects;
- multi-server per-server error collection;
- cache hits, misses, TTL expiry, and command non-caching;
- command-flow previews and missing template placeholders;
- Discord payload dictionaries without importing a Discord library.

Keep top-level import tests updated whenever a new utility module is added.

## Common Mistakes

- Calling the live PRC API from unit tests.
- Sleeping for real production intervals in waiter/watcher tests.
- Testing webhook verification with JSON strings instead of raw bytes.
- Asserting exact `.to_dict()` output when the test only needs one field.
- Letting a rule, cache, or command-flow test call `api.command()` accidentally.

## Related Pages

- [Typed vs Raw Responses](./Typed-vs-Raw-Responses.md)
- [Custom Commands Reference](./Custom-Commands-Reference.md)
- [Waiters and Watchers](./Waiters-and-Watchers.md)

---

[Previous Page: Error Handling and Troubleshooting](./Error-Handling-and-Troubleshooting.md) | [Next Page: Migration to v2](./Migration-to-v2.md)
