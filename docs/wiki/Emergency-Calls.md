# Emergency Calls

PRC v2 exposes emergency calls through `EmergencyCalls=true`, and event
webhooks can push emergency-call lifecycle events. `erlc_api.emergency` adds
small helper tools for filtering, summaries, and nearest-call workflows.

## Payload Fields

| Field | Model field |
| --- | --- |
| `Team` | `team` |
| `Caller` | `caller` |
| `Players` | `players` |
| `Position` | `position` |
| `StartedAt` | `started_at` |
| `CallNumber` | `call_number` |
| `Description` | `description` |
| `PositionDescriptor` | `position_descriptor` |

## Polling

```python
from erlc_api.emergency import EmergencyCallTools

calls = await api.emergency_calls()
tools = EmergencyCallTools(calls)

unresponded = tools.unresponded()
police = tools.by_team("Police")
summary = tools.summary().to_dict()
```

## Nearest Calls

```python
bundle = await api.server(players=True, emergency_calls=True)
call = EmergencyCallTools(bundle).nearest_to(bundle.players[0])
```

`nearest_to(...)` accepts a player, `PlayerLocation`, emergency call, or simple
coordinate list/tuple. It returns `None` when no comparable coordinates exist.

## Webhooks

Use `erlc_api.webhooks` for signature verification and routing. Use
`EmergencyCallTools` after decoding when you want the same filtering logic for
polling and webhook payloads.

## Common Mistakes

- Treating `Players=[]` as an error. It usually means nobody has responded yet.
- Assuming a call has a caller username; PRC may send a user ID or `None`.
- Comparing coordinates without checking that location data is present.

---

[Previous Page: Vehicle Tools](./Vehicle-Tools.md) | [Next Page: Wanted Stars](./Wanted-Stars.md)
