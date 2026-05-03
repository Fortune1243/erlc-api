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

## Preserved Payload Data

Models keep three important forms:

| Attribute | Purpose |
| --- | --- |
| `.raw` | Original endpoint object for that model. |
| `.extra` | Unknown fields not consumed by the typed model. |
| `.to_dict()` | JSON-safe dictionary using model field names. |

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
- Ignoring `.extra` when investigating new fields.
- Mutating `.raw` and expecting frozen model fields to change.

## Related Pages

- [Models Reference](./Models-Reference.md)
- [Endpoint Reference](./Endpoint-Reference.md)
- [Testing and Mocking](./Testing-and-Mocking.md)

---

[Previous Page: Models Reference](./Models-Reference.md) | [Next Page: Commands Reference](./Commands-Reference.md)
