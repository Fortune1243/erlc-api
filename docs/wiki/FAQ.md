# FAQ

## Is this an official PRC SDK?

No. This is an independent community wrapper for the ER:LC PRC Private Server API.

## Why choose this over a thin endpoint wrapper?

Because production workloads need more than endpoint forwarding: rate-limit coordination, retry strategy, multi-server routing, and safer operational defaults.

## Can I use one client for multiple servers?

Yes. Create separate contexts with `client.ctx(server_key)` and reuse one shared `ERLCClient`.

## Does it support both v1 and v2?

Yes. Both `client.v1` and `client.v2` are supported, including typed variants.

## Does typed mode replace raw mode?

No. Raw mode remains fully available. Typed mode is additive.

## Why is `:log` blocked in `client.v1.command(...)`?

To avoid promoting patterns where command execution is overloaded for logging workflows. Use command log retrieval and helper parsing instead.

## How do I safely validate keys in setup flows?

Use `await client.validate_key(ctx)` and branch on `ValidationResult.status`.

## Can I use this for websites/dashboards?

Yes. Use `erlc_api.web` DTO and metrics helpers for backend-friendly shaping.

## How do I publish this wiki?

Use `scripts/publish_wiki.ps1` (PowerShell) or `scripts/publish_wiki.sh` (bash). Both sync from `docs/wiki/` to the GitHub wiki repository.

## Next Steps

- See concrete positioning in [Comparison-and-Why-erlc-api.md](./Comparison-and-Why-erlc-api.md)
- Go back to [Home.md](./Home.md)
