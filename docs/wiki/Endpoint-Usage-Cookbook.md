# Endpoint Usage Cookbook

Fetch the common dashboard view:

```python
bundle = await api.server(players=True, queue=True, staff=True)
```

Fetch everything supported by `GET /v2/server`:

```python
bundle = await api.server(all=True)
```

Send a command:

```python
from erlc_api import cmd

await api.command("h hello")
await api.command(cmd.pm("Player", "hello"))
```

Fetch raw JSON:

```python
payload = await api.server(all=True, raw=True)
```

Use the low-level request method for a newly added API endpoint:

```python
payload = await api.request("GET", "/v2/server", params={"Players": "true"})
```

Use utility tool objects only when needed:

```python
from erlc_api.find import Finder
from erlc_api.analytics import Analyzer

bundle = await api.server(all=True)
player = Finder(bundle).player("Avi")
summary = Analyzer(bundle).dashboard()
```

---

← [Endpoint Reference](./Endpoint-Reference.md) | [Models Reference](./Models-Reference.md) →
