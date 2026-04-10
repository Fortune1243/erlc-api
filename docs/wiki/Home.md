# erlc-api Wiki

This wiki is the practical playbook for shipping ER:LC integrations quickly and safely with `erlc-api`.

`erlc-api` is built for real production bot and backend workloads, not just simple endpoint forwarding:

- async-first client design
- multi-server context routing from one client
- bucket-aware rate-limit coordination
- retry safety (idempotent requests only)
- raw + typed response surfaces
- Discord and web utility layers to reduce glue code

## Start Here

- [Getting-Started.md](./Getting-Started.md)
- [Quickstart-Discord.py.md](./Quickstart-Discord.py.md)
- [Quickstart-Web-Backend.md](./Quickstart-Web-Backend.md)
- [Endpoint-Usage-Cookbook.md](./Endpoint-Usage-Cookbook.md)
- [Typed-vs-Raw-Responses.md](./Typed-vs-Raw-Responses.md)
- [Rate-Limits-Retries-and-Reliability.md](./Rate-Limits-Retries-and-Reliability.md)
- [Error-Handling-and-Troubleshooting.md](./Error-Handling-and-Troubleshooting.md)
- [FAQ.md](./FAQ.md)
- [Comparison-and-Why-erlc-api.md](./Comparison-and-Why-erlc-api.md)

## Recommended Learning Path

1. Install and initialize the client in [Getting-Started.md](./Getting-Started.md).
2. Follow the Discord-first onboarding in [Quickstart-Discord.py.md](./Quickstart-Discord.py.md).
3. Add typed responses and utilities from [Typed-vs-Raw-Responses.md](./Typed-vs-Raw-Responses.md).
4. Harden your deployment using [Rate-Limits-Retries-and-Reliability.md](./Rate-Limits-Retries-and-Reliability.md) and [Error-Handling-and-Troubleshooting.md](./Error-Handling-and-Troubleshooting.md).

## External Docs

- Project README: [README.md](https://github.com/Fortune1243/erlc-api/blob/main/README.md)
- Full comparison matrix: [comparision.md](https://github.com/Fortune1243/erlc-api/blob/main/comparision.md)

## Next Steps

- Continue with [Getting-Started.md](./Getting-Started.md)
- Or jump directly to [Quickstart-Discord.py.md](./Quickstart-Discord.py.md)
