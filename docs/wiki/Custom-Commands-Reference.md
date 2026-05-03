# Custom Commands Reference

PRC Event Webhooks currently send messages that start with `;` so integrations
can create custom in-game commands. `erlc_api.webhooks` remains the low-level
signature verification and event decoding layer. `erlc_api.custom_commands` is a
small, framework-neutral router built on top of that parsed webhook data.

Reference: [PRC Event Webhook docs](https://apidocs.policeroleplay.community/for-developers/v2-api-reference/event-webhook)

## Import

```python
from erlc_api.custom_commands import CustomCommandRouter
```

The module is lazy and not imported by top-level `import erlc_api`.

## CustomCommandRouter

Signature:

```python
CustomCommandRouter(
    *,
    prefix: str = ";",
    case_sensitive: bool = False,
    unknown_handler: CommandHandler | None = None,
)
```

Purpose: route webhook custom command messages to sync or async handlers.

Methods:

| Method | Return type | Purpose |
| --- | --- | --- |
| `command(*names, predicate=None, description=None)` | decorator | Register a command with aliases. |
| `use(middleware)` | middleware | Register middleware that may short-circuit. |
| `on_unknown(handler)` | handler | Register fallback for unmatched commands. |
| `parse_text(text)` | `CustomCommandInvocation | None` | Parse raw message text. |
| `decode(payload)` | `WebhookEvent` | Decode raw webhook payload using router prefix. |
| `context(payload_or_event)` | `CustomCommandContext | None` | Build handler context. |
| `dispatch(payload_or_event)` | `Any` | Async dispatch; returns handler result as-is. |
| `help()` | `list[dict[str, Any]]` | Return route names and descriptions. |

Minimal example:

```python
from erlc_api.custom_commands import CustomCommandRouter

router = CustomCommandRouter(prefix=";")


@router.command("ping", "p", description="Health check")
async def ping(ctx):
    return ctx.reply("pong")


result = await router.dispatch({"Message": ";p"})
```

Common mistakes:

- Using this module as a signature verifier. Verify webhooks with
  `erlc_api.webhooks.assert_valid_event_webhook_signature`.
- Expecting a Discord dependency. This module returns plain Python objects.

## CustomCommandContext

Fields and helpers:

| Member | Type | Purpose |
| --- | --- | --- |
| `invocation` | `CustomCommandInvocation` | Parsed command data from webhooks. |
| `event` | `WebhookEvent` | Decoded webhook event. |
| `raw` | `Mapping[str, Any]` | Original webhook payload. |
| `name` | `str` | Command name as sent. |
| `key` | `str` | Normalized command key. |
| `args` | `tuple[str, ...]` | Parsed command arguments. |
| `text` | `str` | Command text without prefix. |
| `arg(index, default=None)` | `str | None` | Safe positional arg lookup. |
| `rest(start=0)` | `str` | Remaining args joined by spaces. |
| `reply(content=None, data=None, ephemeral=False, **extra)` | `CustomCommandResponse` | Optional response helper. |

Example:

```python
@router.command("warn")
async def warn(ctx):
    target = ctx.arg(0)
    reason = ctx.rest(1)
    if not target or not reason:
        return ctx.reply("usage: ;warn <player> <reason>", ephemeral=True)
    return {"target": target, "reason": reason}
```

## Predicates

Predicates receive `(invocation, context)` and return `True` when the route is
allowed to match. They may be sync or async when used through `dispatch()`.

```python
def has_arg(invocation, ctx):
    return ctx.arg(0) is not None


@router.command("staff", predicate=has_arg)
def staff(ctx):
    return {"ok": True}
```

Predicates are intentionally user-defined. The wrapper does not invent PRC
permissions or Discord role rules.

## Middleware

Middleware runs before route matching. Return `None` to continue, or return any
value to stop dispatch.

```python
@router.use
def block_disabled(ctx):
    if ctx.name in {"shutdown", "restart"}:
        return ctx.reply("That command is disabled.", ephemeral=True)
    return None
```

## Unknown Handler

```python
@router.on_unknown
def unknown(ctx):
    return ctx.reply(f"Unknown command: {ctx.name}", ephemeral=True)
```

If no unknown handler exists, unmatched commands return `None`.

## FastAPI-style Endpoint

```python
from fastapi import FastAPI, HTTPException, Request
from erlc_api.custom_commands import CustomCommandRouter
from erlc_api.webhooks import WebhookError, assert_valid_event_webhook_signature

app = FastAPI()
router = CustomCommandRouter(prefix=";")


@router.command("ping", "p")
async def ping(ctx):
    return ctx.reply("pong")


@app.post("/erlc/events")
async def erlc_events(request: Request):
    raw_body = await request.body()
    try:
        assert_valid_event_webhook_signature(raw_body=raw_body, headers=request.headers)
    except WebhookError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    payload = await request.json()
    result = await router.dispatch(payload)
    return result.to_dict() if hasattr(result, "to_dict") else {"result": result}
```

## Using A Closed-over API Client

The router does not require an `AsyncERLC` or `ERLC` client. Close over your
client when a handler needs to call PRC.

```python
from erlc_api import AsyncERLC, cmd
from erlc_api.custom_commands import CustomCommandRouter

api = AsyncERLC("server-key")
router = CustomCommandRouter()


@router.command("announce", "a")
async def announce(ctx):
    message = ctx.rest()
    result = await api.command(cmd.h(message))
    return ctx.reply(result.message or "sent")
```

---

[Webhooks Reference](./Webhooks-Reference.md) | [Errors and Rate Limits](./Errors-and-Rate-Limits.md)
