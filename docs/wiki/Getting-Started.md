# Getting Started

Use this page to get from zero to first successful ER:LC request quickly.

## Requirements

- Python 3.11+
- A valid ER:LC server key
- Async runtime (`asyncio`)

## Install

```bash
pip install git+https://github.com/Fortune1243/erlc-api.git
```

For local development:

```bash
pip install -e .[dev]
```

## First Successful Call

```python
import asyncio
from erlc_api import ERLCClient


async def main() -> None:
    client = ERLCClient()
    await client.start()
    try:
        ctx = client.ctx("your-server-key")
        status = await client.v1.server(ctx)
        print(status)
    finally:
        await client.close()


asyncio.run(main())
```

## Choose Your Response Mode

- Raw mode: use `client.v1.*` and `client.v2.*` when you want direct JSON pass-through.
- Typed mode: use `*_typed` methods when you want structured dataclasses and better editor/type support.

## Validate Your Key During Setup

```python
result = await client.validate_key(ctx)
if result.status != "ok":
    print("key validation failed:", result.status)
```

## Next Steps

- Build your bot flow with [Quickstart-Discord.py.md](./Quickstart-Discord.py.md)
- Learn endpoint patterns in [Endpoint-Usage-Cookbook.md](./Endpoint-Usage-Cookbook.md)
