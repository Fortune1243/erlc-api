# Event Webhooks and Custom Commands

This guide helps you build an endpoint that:

1. verifies PRC Event Webhook signatures safely
2. receives in-game custom commands starting with `;`
3. routes commands to your own app handlers

Reference: [PRC Event Webhook docs](https://apidocs.policeroleplay.community/for-developers/v2-api-reference/event-webhook)

For command-specific alias, middleware, predicate, and unknown-handler routing,
prefer [Custom Commands Reference](./Custom-Commands-Reference.md). This page
shows the lower-level mixed event router.

## 1. Install webhook support

```
pip install "erlc-api.py[webhooks]"
```

## 2. Build a secure FastAPI endpoint

```python
from fastapi import FastAPI, HTTPException, Request
from erlc_api.webhooks import (
    EventWebhookRouter,
    WebhookEventType,
    assert_valid_event_webhook_signature,
)

app = FastAPI()
router = EventWebhookRouter(command_prefix=";")


@router.on_command("ping")
def handle_ping(command, event):
    return {"reply": "pong", "args": list(command.args)}


@router.on_command("warn")
async def handle_warn(command, event):
    if not command.args:
        return {"ok": False, "error": "usage: ;warn <player> <reason>"}
    return {"ok": True, "target": command.args[0], "reason": " ".join(command.args[1:])}


@router.on_emergency_call()
def handle_emergency(event):
    data = event.emergency_call or {}
    return {"team": data.get("Team"), "caller": data.get("Caller")}


@router.on_unknown()
def handle_unknown(event):
    return {"ok": False, "event_type": event.event_type}


@app.post("/erlc/events")
async def erlc_event_webhook(request: Request):
    raw_body = await request.body()

    try:
        assert_valid_event_webhook_signature(
            raw_body=raw_body,
            headers=request.headers,
            max_skew_s=300,  # set None to disable skew check
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    payload = await request.json()
    results = await router.dispatch(payload)
    return {"handled_results": results}
```

## 3. Verification rules you must keep

- Always verify using raw bytes from `await request.body()`.
- Signature input is `timestamp + raw_body` with no separator.
- Read both required headers: `X-Signature-Timestamp` and `X-Signature-Ed25519`.
- Return non-2xx for invalid signatures.

## 4. Useful helper functions

- `verify_event_webhook_signature(...)` returns `True/False`.
- `assert_valid_event_webhook_signature(...)` raises typed errors.
- `decode_event_webhook_payload(...)` normalizes event shape using explicit type fields plus fallback heuristics.
- `parse_custom_command_text(";ban \"Player One\" rdm")` parses command name and args.

## 5. Common beginner mistakes

- Parsing JSON first and then verifying a re-serialized body.
- Forgetting to install `.[webhooks]` for Ed25519 verification.
- Assuming a fixed webhook payload schema; keep unknown fields and code defensively.
- Returning `2xx` on failed signature checks.

## 6. Next improvements you can add

1. Add role/permission checks before executing command handlers.
2. Add idempotency keys for repeated webhook deliveries.
3. Log command handler outcomes to your moderation audit tables.
4. Use `erlc_api.cache.AsyncCachedClient` for read-only lookups inside handlers.
5. Use `erlc_api.diagnostics` and `erlc_api.discord_tools` for readable handler failures.

Example read-only cache inside a handler:

```python
from erlc_api.cache import AsyncCachedClient

cached_api = AsyncCachedClient(api, ttl_s=5)

@router.on_command("players")
async def handle_players(command, event):
    players = await cached_api.players()
    return {"players": [player.name for player in players]}
```

Keep command execution explicit through the original client and protect it with
your own auth/predicate checks plus `CommandPolicy`:

```python
from erlc_api import CommandPolicy, cmd

announce_policy = CommandPolicy(allowed={"h"}, max_length=120)
safe_command = announce_policy.validate(cmd.h("hello"))
result = await api.command(safe_command)
```

## Related Pages

- [Earlier in the guide: Webhooks Reference](./Webhooks-Reference.md)
- [Workflow Utilities Reference](./Workflow-Utilities-Reference.md)
- [Next in the guide: Custom Commands Reference](./Custom-Commands-Reference.md)

---

[Previous Page: Webhooks Reference](./Webhooks-Reference.md) | [Next Page: Custom Commands Reference](./Custom-Commands-Reference.md)
