# erlc-api Wiki

This wiki is the practical playbook for shipping ER:LC bot/backend integrations with `erlc-api`.

Current implemented strengths:

- async-first client architecture
- multi-server context routing from one client
- bucket-aware rate limiting with reset-aware pre-acquire
- configurable retry + backoff jitter
- request coalescing for duplicate idempotent GET calls
- TTL cache with manual invalidation and cache stats
- optional per-bucket circuit breaker
- raw + typed + validated v2 response modes
- command dry-run/tracking + log stream helpers
- live server tracker callbacks (string + `TrackerEvent` enum names)
- event webhook verification + custom command routing helpers
- metrics sink hooks including command-level emission

## Start Here

- [Getting-Started.md](./Getting-Started.md)
- [Quickstart-Discord.py.md](./Quickstart-Discord.py.md)
- [Quickstart-Web-Backend.md](./Quickstart-Web-Backend.md)
- [Function-List.md](./Function-List.md)
- [Event-Webhooks-and-Custom-Commands.md](./Event-Webhooks-and-Custom-Commands.md)
- [Endpoint-Usage-Cookbook.md](./Endpoint-Usage-Cookbook.md)
- [Typed-vs-Raw-Responses.md](./Typed-vs-Raw-Responses.md)
- [Rate-Limits-Retries-and-Reliability.md](./Rate-Limits-Retries-and-Reliability.md)
- [Error-Handling-and-Troubleshooting.md](./Error-Handling-and-Troubleshooting.md)
- [FAQ.md](./FAQ.md)
- [Comparison-and-Why-erlc-api.md](./Comparison-and-Why-erlc-api.md)

## Recommended Path

1. Initialize client + context in [Getting-Started.md](./Getting-Started.md).
2. Build primary integration from [Quickstart-Discord.py.md](./Quickstart-Discord.py.md) or [Quickstart-Web-Backend.md](./Quickstart-Web-Backend.md).
3. Choose raw/typed/validated mode in [Typed-vs-Raw-Responses.md](./Typed-vs-Raw-Responses.md).
4. Harden reliability from [Rate-Limits-Retries-and-Reliability.md](./Rate-Limits-Retries-and-Reliability.md) and [Error-Handling-and-Troubleshooting.md](./Error-Handling-and-Troubleshooting.md).

## External Docs

- Project README: [README.md](https://github.com/Fortune1243/erlc-api/blob/main/README.md)
- Full comparison matrix: [comparision.md](https://github.com/Fortune1243/erlc-api/blob/main/comparision.md)
