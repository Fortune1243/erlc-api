# Quickstart: Web Backend

```python
from fastapi import FastAPI
from erlc_api import AsyncERLC

app = FastAPI()
api = AsyncERLC("server-key")


@app.on_event("startup")
async def startup() -> None:
    await api.start()


@app.on_event("shutdown")
async def shutdown() -> None:
    await api.close()


@app.get("/dashboard")
async def dashboard():
    bundle = await api.server(players=True, queue=True, staff=True)
    return bundle.to_dict()
```

