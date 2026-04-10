# Comparison and Why `erlc-api`

If your goal is to ship reliable Discord bot or backend features faster, `erlc-api` is built to win on operational developer experience.

## Where `erlc-api` is strongest

- Native async architecture for modern Python service stacks.
- Multi-server context model from a single client instance.
- Bucket-aware rate-limit logic and retry behavior tuned for production usage.
- Clear non-idempotent command safety (no automatic command replay).
- Dual response surfaces (raw + typed) so teams can pick speed or structure per endpoint.
- Discord and web utility modules that remove repetitive app-level glue code.

## Executive capability snapshot

| Capability | `erlc-api` stance |
|---|---|
| Async-first runtime | Native and primary architecture |
| Multi-server handling | First-class via `ERLCContext` |
| Typed and raw responses | Both supported, additive |
| Production retry strategy | Built in, idempotent-aware |
| Discord/web integration help | Included utilities/adapters |

For a full matrix, see: [comparision.md](https://github.com/Fortune1243/erlc-api/blob/main/comparision.md)

## Why teams move faster with this wrapper

- Less custom retry/rate-limit code to maintain.
- Cleaner bot architecture for multi-community deployments.
- Better maintainability with typed models where it matters.
- Faster web API shaping with DTO + metrics helpers.

## Positioning principle

We favor strong claims that can be verified in code and docs. If a capability is listed here, it is backed by implemented behavior in this repository.

## Next Steps

- Start implementation from [Quickstart-Discord.py.md](./Quickstart-Discord.py.md)
- Review reliability internals in [Rate-Limits-Retries-and-Reliability.md](./Rate-Limits-Retries-and-Reliability.md)
