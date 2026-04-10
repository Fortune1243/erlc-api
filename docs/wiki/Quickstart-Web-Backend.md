# Quickstart (Web Backend)

Use this pattern for dashboards/panels/internal APIs.

## FastAPI example

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
            "cache": api_client.cache_stats(),
        }
    except ERLCError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
```

## Optional validated mode endpoint

```python
@app.get("/servers/{server_key}/snapshot-validated")
async def snapshot_validated(server_key: str):
    ctx = api_client.ctx(server_key)
    bundle = await api_client.v2.server_default_validated(ctx, strict=False)
    return bundle.model_dump()
```

## Operational helpers

- `api_client.invalidate(ctx, endpoint=None)` to clear stale cache entries.
- `api_client.request_replay(limit=...)` for redacted request trace inspection.
- `api_client.track_server(...)` if you need push-like state aggregation.

## Why this helps

- Stable DTOs for frontend contracts.
- Typed/validated decoding lowers shape bugs.
- Built-in reliability controls reduce custom middleware.
