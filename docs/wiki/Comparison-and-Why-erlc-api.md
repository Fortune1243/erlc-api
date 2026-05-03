# Comparison and Why erlc-api

`erlc-api` v2.0 focuses on the smallest useful wrapper surface:

- sync and async clients
- flat method names
- v2-first endpoint behavior
- typed dataclasses by default
- `raw=True` escape hatch
- minimal safe rate-limit handling
- retained pure utilities and webhook helpers

The package intentionally avoids heavyweight runtime features such as cache backends, metrics sinks, tracing, request replay, and circuit breakers.


---

← [Migration to v2](./Migration-to-v2.md)
