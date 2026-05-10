from __future__ import annotations

import asyncio

from erlc_api import AsyncClient


async def main() -> None:
    async with AsyncClient.from_env() as api:
        bundle = await api.bundle()
        print(bundle.name or "Unnamed server")
        print(f"Players: {len(bundle.players_list)}")
        print(f"Queue: {len(bundle.queue_list)}")
        print(f"Staff: {len(bundle.staff_members)}")
        print(f"Vehicles: {len(bundle.vehicles_list)}")


if __name__ == "__main__":
    asyncio.run(main())
