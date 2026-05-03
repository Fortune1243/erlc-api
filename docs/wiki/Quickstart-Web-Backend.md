# Quickstart: Web Backend

This guide walks you through building a small FastAPI service that exposes ERLC server data over HTTP. By the end you will have four endpoints: `GET /status`, `GET /players`, `GET /staff`, and `POST /announce`.

## 1. Prerequisites

- Install the required packages:
  ```
  pip install erlc-api.py fastapi uvicorn
  ```
- A PRC server key — see [Clients and Authentication](./Clients-and-Authentication.md) for how to obtain one.

## 2. Client lifecycle

Use FastAPI's `lifespan` context manager to start and close `AsyncERLC` alongside the app. This replaces the deprecated `@app.on_event("startup"/"shutdown")` approach.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from erlc_api import AsyncERLC, cmd

api = AsyncERLC("your-server-key")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await api.start()
    yield
    await api.close()


app = FastAPI(lifespan=lifespan)
```

## 3. Endpoints

### `GET /status` — server overview

```python
@app.get("/status")
async def status():
    info = await api.server()
    return {
        "name": info.name,
        "players": info.current_players,
        "max_players": info.max_players,
    }
```

### `GET /players` — list online players

```python
@app.get("/players")
async def players():
    online = await api.players()
    return [{"name": p.name, "team": p.team, "user_id": p.user_id} for p in online]
```

### `GET /staff` — staff on duty

```python
@app.get("/staff")
async def staff():
    duty = (await api.staff()).members()
    return [{"name": m.name, "role": str(m.role)} for m in duty]
```

### `POST /announce` — broadcast a hint

```python
from pydantic import BaseModel

class AnnounceBody(BaseModel):
    message: str

@app.post("/announce")
async def announce(body: AnnounceBody):
    result = await api.command(cmd.h(body.message))
    return {"ok": True, "message": result.message}
```

## 4. Error handling

Convert API errors to proper HTTP responses using `HTTPException`.

```python
from fastapi import HTTPException
from erlc_api import AuthError, RateLimitError, ERLCError

@app.get("/status")
async def status():
    try:
        info = await api.server()
        return {"name": info.name, "players": info.current_players, "max_players": info.max_players}
    except AuthError:
        raise HTTPException(status_code=401, detail="Invalid server key.")
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=f"Rate limited. Retry after {e.retry_after:.0f}s.")
    except ERLCError as e:
        raise HTTPException(status_code=502, detail=str(e))
```

## 5. Running the server

```
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. FastAPI generates interactive docs at `/docs` automatically.

## 6. Common mistakes

- **Using `@app.on_event("startup"/"shutdown")`.** These are deprecated in modern FastAPI. Use the `lifespan` context manager instead.
- **Sharing one `AsyncERLC` instance across threads.** The client is not thread-safe; use it only within the async event loop FastAPI runs on.
- **Returning model objects directly.** `erlc_api` models are dataclasses, not Pydantic models. Call `.to_dict()` or map fields manually before returning from a route.
- **Not handling `RateLimitError`.** ERLC enforces per-endpoint limits. Without handling, FastAPI returns a 500 to the caller instead of a meaningful 429.
- **Starting the client outside `lifespan`.** Calling `await api.start()` at module level runs before an event loop exists and will raise a runtime error.

## 7. Next steps

- [Endpoint Reference](./Endpoint-Reference.md) — full list of available endpoints (`kill_logs`, `bans`, `vehicles`, etc.)
- [Commands Reference](./Commands-Reference.md) — all supported in-game commands via `cmd.*`
- [Event Webhooks and Custom Commands](./Event-Webhooks-and-Custom-Commands.md) — receive in-game events pushed to your backend
- [Waiters and Watchers](./Waiters-and-Watchers.md) — poll for changes and build live-update features

---

← [Quickstart: Discord.py](./Quickstart-Discord.py.md) | [Migration to v2](./Migration-to-v2.md) →
