# Wanted Stars

PRC v2 player payloads include `WantedStars`. `erlc-api.py` parses this into
`Player.wanted_stars` and exposes filters, finders, sorters, and watcher events.

## Filtering

```python
from erlc_api.filter import Filter
from erlc_api.find import Finder

wanted = Filter(players).wanted().all()
high_priority = Filter(players).wanted(stars=3).all()
same = Finder(players).wanted(stars=1)
```

## Sorting

```python
from erlc_api.sort import Sorter

top_wanted = Sorter(players).wanted_stars().first()
```

## Watcher Events

`AsyncWatcher` and `Watcher` emit:

| Event | Meaning |
| --- | --- |
| `wanted_new` | Player went from 0 to more than 0 stars. |
| `wanted_cleared` | Player went from wanted to 0 stars. |
| `wanted_escalated` | Wanted level increased. |
| `wanted_decreased` | Wanted level decreased but stayed above 0. |
| `wanted_change` | Any wanted-star change. |

```python
from erlc_api.watch import AsyncWatcher

async for event in AsyncWatcher(api).events():
    if event.type == "wanted_new":
        print(event.item.name, event.item.wanted_stars)
```

## Common Mistakes

- Treating `None` as wanted. Helpers treat missing values as `0`.
- Polling too aggressively for wanted changes. Use default rate limiting and
  conservative watcher intervals.

---

[Previous Page: Emergency Calls](./Emergency-Calls.md) | [Next Page: Ops Utilities Reference](./Ops-Utilities-Reference.md)
