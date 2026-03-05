import asyncio
import os

from erlc_api import ERLCClient

ENV_KEY = "ERLC_SERVER_KEY"
KEY = os.getenv(ENV_KEY, "").strip()

if not KEY:
    raise SystemExit(f"Missing required environment variable: {ENV_KEY}")

async def main():
    client = ERLCClient()
    try:
        await client.start()

        ctx = client.ctx(KEY)

        result = await client.validate_key(ctx)
        print("validate_key:", result)

        server = await client.v1.server(ctx)
        print("server:", server)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
