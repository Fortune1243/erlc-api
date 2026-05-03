# Typed vs Raw Responses

Typed dataclasses are the default:

```python
players = await api.players()
print(players[0].name, players[0].user_id)
```

Use `raw=True` when you need the exact API JSON:

```python
payload = await api.players(raw=True)
print(payload[0]["Player"])
```

Typed models preserve unknown fields through `.extra` and include `.raw` plus `.to_dict()`.

