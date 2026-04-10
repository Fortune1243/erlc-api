# Typed vs Raw Responses

`erlc-api` gives you both response modes so you can optimize for speed or structure per use case.

## Quick decision guide

| Mode | Use when | Tradeoff |
|---|---|---|
| Raw (`client.v1.*`, `client.v2.*`) | You need full pass-through JSON control | More manual field handling |
| Typed (`*_typed`) | You want stable dataclasses and clearer app code | Top-level decode validation can raise `ModelDecodeError` |

## Side-by-side example

```python
# Raw
raw_players = await client.v1.players(ctx)
first_name_raw = raw_players[0].get("Player") if raw_players else None

# Typed
typed_players = await client.v1.players_typed(ctx)
first_name_typed = typed_players[0].name if typed_players else None
```

## Decode behavior you can rely on

- Top-level shape is validated (object vs list).
- Missing nested fields are set to `None`.
- Unknown fields are preserved in each model's `extra`.
- Timestamps remain epoch integers with datetime helper properties.

## Handling typed decode failures

```python
from erlc_api import ModelDecodeError

try:
    bundle = await client.v2.server_default_typed(ctx)
except ModelDecodeError as exc:
    print("unexpected payload shape:", exc)
```

## Next Steps

- Learn reliability guarantees in [Rate-Limits-Retries-and-Reliability.md](./Rate-Limits-Retries-and-Reliability.md)
- Compare wrapper strengths in [Comparison-and-Why-erlc-api.md](./Comparison-and-Why-erlc-api.md)
