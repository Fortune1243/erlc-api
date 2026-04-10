# Getting Started

Use this page to get from zero to a reliable first integration.

## Requirements

- Python 3.11+
- Valid ER:LC server key
- Async runtime (`asyncio`)

## Install

```bash
pip install git+https://github.com/Fortune1243/erlc-api.git
```

Local development:

```bash
pip install -e .[dev]
```

Optional extras:

```bash
pip install -e .[pydantic]       # validated v2 models
pip install -e .[redis]          # redis cache backend
pip install -e .[observability]  # structlog + opentelemetry-api
```

## First Successful Call

```python
import asyncio
from erlc_api import ERLCClient


async def main() -> None:
    async with ERLCClient() as client:
        ctx = client.ctx("your-server-key")
        status = await client.v1.server(ctx)
        print(status)


asyncio.run(main())
```

## Choose Response Mode

- Raw: `client.v1.*`, `client.v2.*`
- Typed dataclass: `*_typed`
- Validated v2 (Pydantic): `*_validated(..., strict=False)`

## Validate Keys During Setup

```python
result = await client.validate_key(ctx)
if result.status != "ok":
    print("validation failed:", result.status)
```

## Useful Operational APIs

```python
print(client.cache_stats())
print(client.request_replay(limit=10))
await client.invalidate(ctx, "/v1/server/players")
```

## Next Steps

- Bot path: [Quickstart-Discord.py.md](./Quickstart-Discord.py.md)
- Backend path: [Quickstart-Web-Backend.md](./Quickstart-Web-Backend.md)
- Reliability deep dive: [Rate-Limits-Retries-and-Reliability.md](./Rate-Limits-Retries-and-Reliability.md)
