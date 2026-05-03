# Getting Started

Install:

```bash
pip install erlc-api
```

Async:

```python
from erlc_api import AsyncERLC

async with AsyncERLC("server-key") as api:
    players = await api.players()
    print(players[0].name)
```

Sync:

```python
from erlc_api import ERLC

with ERLC("server-key") as api:
    print(api.server())
```

Override the default key per call:

```python
await api.players(server_key="other-key")
```

Use `global_key=` when the PRC large-app flow gives your app an Authorization key.

