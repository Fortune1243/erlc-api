import asyncio
import os

from erlc_api import AsyncERLC


ENV_KEY = "ERLC_SERVER_KEY"


async def main() -> None:
    key = os.getenv(ENV_KEY, "").strip()
    if not key:
        raise SystemExit(f"Missing required environment variable: {ENV_KEY}")

    async with AsyncERLC(key) as api:
        print("validate_key:", await api.validate_key())
        print("server:", await api.server(raw=True))


if __name__ == "__main__":
    asyncio.run(main())

