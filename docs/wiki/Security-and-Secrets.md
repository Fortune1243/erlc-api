# Security and Secrets

This page covers safe handling for server keys, global authorization keys,
webhook signatures, and logs.

## Key Types

| Key | Sent as | Use |
| --- | --- | --- |
| Server key | `Server-Key` | Required for server API requests. |
| Global key | `Authorization` | Optional PRC large-app authorization flow. |

Create clients with explicit values or environment variables:

```python
import os
from erlc_api import AsyncERLC

api = AsyncERLC(
    os.environ["ERLC_SERVER_KEY"],
    global_key=os.environ.get("ERLC_GLOBAL_KEY"),
)
```

## Secret Storage

Prefer environment variables, deployment secrets, or your platform secret store.
Do not commit server keys to source control.

Suggested environment names:

```text
ERLC_SERVER_KEY
ERLC_GLOBAL_KEY
ERLC_WEBHOOK_SECRET_CONTEXT
```

The wrapper does not require these exact names; they are conventions for your
application.

## Logging Redaction

Do not log:

- `Server-Key`;
- `Authorization`;
- raw request headers;
- full request objects from frameworks;
- webhook raw bodies when they may include private moderation text.

Log safe context instead:

```python
try:
    await api.players()
except Exception as exc:
    logger.warning("ERLC request failed: %s", exc)
```

Wrapper exceptions expose short body excerpts and request metadata without
requiring secret headers.

## Webhook Verification

Verify the raw request body before trusting JSON:

```python
from erlc_api.webhooks import WebhookError, assert_valid_event_webhook_signature


async def handler(request):
    raw_body = await request.body()
    try:
        assert_valid_event_webhook_signature(raw_body=raw_body, headers=request.headers)
    except WebhookError:
        return {"ok": False}, 401

    payload = await request.json()
    return {"ok": True, "payload": payload}
```

Important rules:

- Use the exact raw bytes from the request.
- Do not reserialize JSON before verification.
- Reject invalid signatures with a non-2xx response.
- Keep timestamp skew checks enabled unless your deployment requires otherwise.

## Command Safety

The wrapper normalizes command syntax, but it does not invent PRC permissions or
Discord role policies. Put application-level checks in your bot, web route,
middleware, or custom command predicate.

```python
@router.command("announce", predicate=lambda _invocation, ctx: ctx.arg(0) is not None)
async def announce(ctx):
    ...
```

## Common Mistakes

- Printing `api` objects or request headers in logs.
- Verifying webhook signatures after parsing JSON.
- Treating `global_key` as a replacement for `server_key`.
- Building a public web endpoint that executes commands without app-level auth.

## Related Pages

- [Clients and Authentication](./Clients-and-Authentication.md)
- [Webhooks Reference](./Webhooks-Reference.md)
- [Custom Commands Reference](./Custom-Commands-Reference.md)

---

[Previous Page: Custom Commands Reference](./Custom-Commands-Reference.md) | [Next Page: Rate Limits, Retries, and Reliability](./Rate-Limits-Retries-and-Reliability.md)
