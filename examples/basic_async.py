from __future__ import annotations

import asyncio

from erlc_api import AsyncClient


async def main() -> None:
    async with AsyncClient.from_env() as api:
        players = await api.players()
        print(f"{len(players)} player(s) online")
        for player in players:
            print(f"- {player.name} ({player.user_id})")


if __name__ == "__main__":
    asyncio.run(main())
