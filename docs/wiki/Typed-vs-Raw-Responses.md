# Typed vs Raw Responses

Endpoint methods return typed dataclasses by default. Pass `raw=True` when you
need exact PRC JSON for debugging, compatibility checks, or unsupported fields.

## Typed Responses

```python
players = await api.players()
first = players[0]

print(first.name, first.user_id, first.team)
print(first.to_dict())
```

Typed responses are best for application code because they provide stable
attribute names, helpers, and conversion back to dictionaries.

## Raw Responses

```python
payload = await api.players(raw=True)
print(payload[0]["Player"])
```

Raw responses are best for diagnostics, examples copied directly from PRC, and
new API fields not yet modeled by the wrapper.

`raw=True` is method-shaped:

| Call | Raw result |
| --- | --- |
| `api.server(raw=True)` | Full `/v2/server` response body. |
| `api.server(players=True, raw=True)` | Full `/v2/server` response body, including `Players`. |
| `api.players(raw=True)` | Raw `Players` section list only. |
| `api.staff(raw=True)` | Raw `Staff` section object only. |
| `api.queue(raw=True)` | Raw `Queue` section list only. |
| `api.join_logs(raw=True)` and other section helpers | That raw section list only. |
| `api.bans(raw=True)` | Raw v1 bans mapping. |
| `api.command(raw=True)` | Raw v2 command response. |
| `api.request(...)` | Raw decoded response body. |

## Preserved Payload Data

Models keep three important forms:

| Attribute | Purpose |
| --- | --- |
| `.raw` | Original endpoint object for that model. |
| `.extra` | Unknown fields not consumed by the typed model. |
| `.to_dict()` | JSON-safe dictionary using wrapper model field names. |

Example:

```python
player = (await api.players())[0]
print(player.raw)
print(player.extra)
print(player.to_dict())
```

## Choosing A Mode

Use typed responses when:

- building bots, dashboards, scripts, or services;
- filtering, sorting, grouping, or exporting data;
- sharing models across your codebase.

Use `raw=True` when:

- filing a bug report;
- checking if PRC added a field;
- comparing wrapper output to official examples;
- writing fixture tests around exact payloads.

## Common Mistakes

- Using raw payloads everywhere and reimplementing model parsing.
- Assuming `.to_dict()` is byte-for-byte identical to PRC JSON.
- Expecting `players(raw=True)` to return the full `/v2/server` object. Use
  `server(players=True, raw=True)` for that.
- Ignoring `.extra` when investigating new fields.
- Mutating `.raw` and expecting frozen model fields to change.

## Related Pages

- [Models Reference](./Models-Reference.md)
- [Endpoint Reference](./Endpoint-Reference.md)
- [Testing and Mocking](./Testing-and-Mocking.md)

---

[Previous Page: Models Reference](./Models-Reference.md) | [Next Page: Commands Reference](./Commands-Reference.md)
