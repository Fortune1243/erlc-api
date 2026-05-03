from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncIterator, Generic, TypeVar

from ..client import AsyncERLC
from ..models import Player, ServerBundle
from .diff import PlayerDiff, QueueDiff, ServerDefaultDiff, diff_players, diff_queue, diff_server_default

CurrentT = TypeVar("CurrentT")
DiffT = TypeVar("DiffT")


@dataclass(frozen=True)
class PollSnapshot(Generic[CurrentT, DiffT]):
    current: CurrentT
    previous: CurrentT | None
    diff: DiffT | None
    fetched_at_epoch: float

    @property
    def fetched_at(self) -> datetime:
        return datetime.fromtimestamp(self.fetched_at_epoch, tz=timezone.utc)


def _validate_interval(interval_s: float) -> None:
    if interval_s <= 0:
        raise ValueError("interval_s must be greater than zero.")


async def poll_players(
    client: AsyncERLC,
    *,
    server_key: str | None = None,
    interval_s: float = 5.0,
) -> AsyncIterator[PollSnapshot[list[Player], PlayerDiff]]:
    _validate_interval(interval_s)
    previous: list[Player] | None = None
    while True:
        current = await client.players(server_key=server_key)
        snapshot = PollSnapshot(
            current=current,
            previous=previous,
            diff=diff_players(previous, current) if previous is not None else None,
            fetched_at_epoch=time.time(),
        )
        yield snapshot
        previous = current
        await asyncio.sleep(interval_s)


async def poll_queue(
    client: AsyncERLC,
    *,
    server_key: str | None = None,
    interval_s: float = 5.0,
) -> AsyncIterator[PollSnapshot[list[int], QueueDiff]]:
    _validate_interval(interval_s)
    previous: list[int] | None = None
    while True:
        current = await client.queue(server_key=server_key)
        snapshot = PollSnapshot(
            current=current,
            previous=previous,
            diff=diff_queue(previous, current) if previous is not None else None,
            fetched_at_epoch=time.time(),
        )
        yield snapshot
        previous = current
        await asyncio.sleep(interval_s)


async def poll_server_default(
    client: AsyncERLC,
    *,
    server_key: str | None = None,
    interval_s: float = 5.0,
) -> AsyncIterator[PollSnapshot[ServerBundle, ServerDefaultDiff]]:
    _validate_interval(interval_s)
    previous: ServerBundle | None = None
    while True:
        current = await client.server(server_key=server_key, players=True, queue=True, staff=True)
        snapshot = PollSnapshot(
            current=current,
            previous=previous,
            diff=diff_server_default(previous, current) if previous is not None else None,
            fetched_at_epoch=time.time(),
        )
        yield snapshot
        previous = current
        await asyncio.sleep(interval_s)


__all__ = [
    "PollSnapshot",
    "poll_players",
    "poll_queue",
    "poll_server_default",
]
