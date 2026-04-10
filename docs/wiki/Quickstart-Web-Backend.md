# Quickstart (Web Backend)

Use this pattern when you are building dashboards, panels, or internal APIs on top of ER:LC data.

## FastAPI pattern

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from erlc_api import ERLCClient, ERLCError
from erlc_api.web import compute_dashboard_metrics, v2_bundle_to_dto


api_client = ERLCClient()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await api_client.start()
    try:
        yield
    finally:
        await api_client.close()


app = FastAPI(lifespan=lifespan)


@app.get("/servers/{server_key}/snapshot")
async def snapshot(server_key: str):
    ctx = api_client.ctx(server_key)
    try:
        bundle = await api_client.v2.server_default_typed(ctx)
        return {
            "bundle": v2_bundle_to_dto(bundle),
            "metrics": compute_dashboard_metrics(bundle).__dict__,
        }
    except ERLCError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
```

## Why this is better than raw forwarding

- You get stable DTO conversion for frontend consumers.
- Metrics helpers reduce repeated counting and grouping code.
- Typed responses reduce silent key/shape mistakes in downstream app logic.

## Next Steps

- Expand endpoint usage in [Endpoint-Usage-Cookbook.md](./Endpoint-Usage-Cookbook.md)
- Choose response mode in [Typed-vs-Raw-Responses.md](./Typed-vs-Raw-Responses.md)
