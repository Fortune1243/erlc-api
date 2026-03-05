"""
Safe smoke-test example.

Usage (PowerShell):
  $env:ERLC_SERVER_KEY="your-server-key"
  python scripts/smoke.py
"""

import asyncio
import os

from erlc_api import ERLCClient


ENV_KEY = "ERLC_SERVER_KEY"


async def main() -> None:
    key = os.getenv(ENV_KEY, "").strip()
    if not key:
        raise SystemExit(f"Missing required environment variable: {ENV_KEY}")

    client = ERLCClient()
    try:
        await client.start()
        ctx = client.ctx(key)
        print("validate_key:", await client.validate_key(ctx))
        print("server:", await client.v1.server(ctx))
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
