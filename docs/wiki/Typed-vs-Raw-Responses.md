# Typed vs Raw Responses

`erlc-api` supports three response modes depending on how strict you want your integration to be.

## Decision Guide

| Mode | Use when | Tradeoff |
|---|---|---|
| Raw (`client.v1.*`, `client.v2.*`) | Need full payload pass-through | More manual key handling |
| Typed dataclass (`*_typed`) | Want stable model attributes + additive parsing | Top-level shape mismatch can raise `ModelDecodeError` |
| Validated v2 (`*_validated`) | Need schema validation and stricter guarantees | Requires `pydantic` extra |

## Side-by-side

```python
# Raw
raw_players = await client.v1.players(ctx)

# Typed dataclass
typed_players = await client.v1.players_typed(ctx)

# Validated v2 (pydantic)
bundle = await client.v2.server_default_validated(ctx, strict=False)
```

## Typed v2 field coverage highlights

- Player location: `PlayerLocation` (`LocationX`, `LocationZ`, `PostalCode`, `StreetName`, `BuildingNumber`)
- Wanted stars: `Player.wanted_stars`
- Vehicle color metadata: `Vehicle.color_hex`, `Vehicle.color_name`, `Vehicle.color_info`
- Helpers tier: `V2ServerBundle.helpers`
- Emergency calls: `V2ServerBundle.emergency_calls`

## Decode behavior

- Top-level shape validated (object/list)
- Missing optional fields become `None`
- Unknown fields preserved in each model `extra`
- Timestamp helper properties remain available

## Handling decode issues

```python
from erlc_api import ModelDecodeError

try:
    bundle = await client.v2.server_default_typed(ctx)
except ModelDecodeError:
    bundle_raw = await client.v2.server_default(ctx)
```

## Next Steps

- Reliability controls: [Rate-Limits-Retries-and-Reliability.md](./Rate-Limits-Retries-and-Reliability.md)
- Endpoint examples: [Endpoint-Usage-Cookbook.md](./Endpoint-Usage-Cookbook.md)
