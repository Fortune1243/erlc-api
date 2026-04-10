from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncIterator, Generic, TypeVar

from ..client import ERLCClient
from ..context import ERLCContext
from ..models import Player, QueueEntry, V2ServerBundle
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
    client: ERLCClient,
    ctx: ERLCContext,
    *,
    interval_s: float = 5.0,
) -> AsyncIterator[PollSnapshot[list[Player], PlayerDiff]]:
    _validate_interval(interval_s)
    previous: list[Player] | None = None

    while True:
        current = await client.v1.players_typed(ctx)
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
    client: ERLCClient,
    ctx: ERLCContext,
    *,
    interval_s: float = 5.0,
) -> AsyncIterator[PollSnapshot[list[QueueEntry], QueueDiff]]:
    _validate_interval(interval_s)
    previous: list[QueueEntry] | None = None

    while True:
        current = await client.v1.queue_typed(ctx)
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
    client: ERLCClient,
    ctx: ERLCContext,
    *,
    interval_s: float = 5.0,
) -> AsyncIterator[PollSnapshot[V2ServerBundle, ServerDefaultDiff]]:
    _validate_interval(interval_s)
    previous: V2ServerBundle | None = None

    while True:
        current = await client.v2.server_default_typed(ctx)
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
