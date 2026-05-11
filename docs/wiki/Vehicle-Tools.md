# Vehicle Tools

`erlc_api.vehicles` is a lazy module for working with v2 vehicle payloads. It
adds catalog-aware parsing, plate lookup, owner joins, and summaries without
adding dependencies or changing the base client.

The catalog and ergonomics are inspired by the MIT-licensed vehicle typing work
in `TychoTeam/prc.api-py`, with implementation kept native to `erlc-api.py`.

## Import

```python
from erlc_api.vehicles import VehicleTools, parse_vehicle_name
```

## Model Helpers

`Vehicle` keeps PRC fields and adds computed helpers:

| Helper | Meaning |
| --- | --- |
| `full_name` | Original vehicle name. |
| `model_name` | Name with a leading/trailing year removed when detected. |
| `year` | Parsed model year if present. |
| `owner_name` / `owner_id` | Parsed from `Owner` when possible. |
| `normalized_plate` | Uppercase alphanumeric plate string for matching. |
| `is_secondary` | Catalog guess for ATV, mower, forklift, and similar secondary vehicles. |
| `is_prestige` | Catalog guess for prestige/exotic models. |
| `is_custom_texture` | Texture classification helper. |

## VehicleTools

```python
vehicles = await api.vehicles()
tools = VehicleTools(vehicles)

tools.by_owner("Avi")
tools.by_color("Blue")
tools.by_model("Falcon Advance 350")
tools.find_plate("ABC")
tools.duplicate_plates()
tools.summary().to_dict()
```

For team-aware vehicle queries, pass the current player list:

```python
bundle = await api.server(players=True, vehicles=True)
police_vehicles = VehicleTools(bundle).by_team("Police", players=bundle.players or [])
```

## PlayerVehicleBundle

When a bundle includes both players and vehicles, use `bundle.player_vehicles`:

```python
bundle = await api.server(players=True, vehicles=True)
joined = bundle.player_vehicles

if joined:
    avi = joined.player("Avi")
    owner = joined.vehicle("ABC123").owner_player
```

## Common Mistakes

- Treating catalog guesses as official PRC classifications.
- Assuming every vehicle has a plate, color, owner ID, or known model.
- Using `by_team(...)` without passing player data.

## Related Pages

- [Models Reference](./Models-Reference.md)
- [Workflow Utilities Reference](./Workflow-Utilities-Reference.md)
- [Wanted Stars](./Wanted-Stars.md)

---

[Previous Page: Roblox Utils](./Roblox-Utils.md) | [Next Page: Emergency Calls](./Emergency-Calls.md)
