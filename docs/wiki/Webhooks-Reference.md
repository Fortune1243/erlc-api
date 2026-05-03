# Webhooks Reference

Webhook helpers live in `erlc_api.webhooks`, not top-level `erlc_api`.

Install signature verification support:

```bash
pip install "erlc-api[webhooks]"
```

Use explicit imports:

```python
from erlc_api.webhooks import EventWebhookRouter, assert_valid_event_webhook_signature
```

Reference: [PRC Event Webhook docs](https://apidocs.policeroleplay.community/for-developers/v2-api-reference/event-webhook)

## Signature Verification

### `extract_webhook_signature_headers`

Signature:

```python
extract_webhook_signature_headers(headers: Mapping[str, Any]) -> WebhookSignatureHeaders
```

Purpose: extract `X-Signature-Timestamp` and `X-Signature-Ed25519`.

Return type: `WebhookSignatureHeaders`.

Common mistakes:

- Renaming headers before verification.
- Treating missing headers as an unsupported event instead of invalid request authentication.

### `assert_valid_event_webhook_signature`

Signature:

```python
assert_valid_event_webhook_signature(
    *,
    raw_body: bytes | bytearray | memoryview,
    headers: Mapping[str, Any] | WebhookSignatureHeaders,
    public_key_b64: str = PRC_EVENT_WEBHOOK_PUBLIC_KEY_SPKI_B64,
    max_skew_s: float | None = 300,
    now_epoch_s: float | None = None,
) -> None
```

Purpose: validate PRC Ed25519 webhook signatures and raise on failure.

Return type: `None`.

Minimal example:

```python
from erlc_api.webhooks import assert_valid_event_webhook_signature

raw_body = await request.body()
assert_valid_event_webhook_signature(raw_body=raw_body, headers=request.headers)
```

Important options:

- `raw_body` must be the exact bytes received by your web framework.
- `max_skew_s=None` disables timestamp skew checking.
- `public_key_b64` can be overridden for tests.

Common mistakes:

- Verifying re-serialized JSON instead of the raw request body.
- Catching all exceptions and returning `200`; invalid signatures should return non-2xx.

### `verify_event_webhook_signature`

Signature:

```python
verify_event_webhook_signature(...) -> bool
```

Purpose: boolean wrapper around `assert_valid_event_webhook_signature`.

Minimal example:

```python
ok = verify_event_webhook_signature(raw_body=raw_body, headers=headers)
```

Common mistake: using the boolean helper when you need an error reason. Use the
asserting helper for detailed errors.

## Payload Decoding

### `parse_custom_command_text`

Signature:

```python
parse_custom_command_text(text: str, *, prefix: str = ";") -> CustomCommandInvocation | None
```

Purpose: parse custom command text like `;warn "Player One" RDM`.

Return type: `CustomCommandInvocation | None`.

Minimal example:

```python
from erlc_api.webhooks import parse_custom_command_text

command = parse_custom_command_text(';warn "Player One" RDM')
print(command.command_name, command.args)
```

Common mistakes:

- Expecting a command when the prefix does not match. The function returns `None`.

### `decode_event_webhook_payload`

Signature:

```python
decode_event_webhook_payload(payload: Mapping[str, Any], *, command_prefix: str = ";") -> WebhookEvent
```

Purpose: decode raw webhook JSON into a typed `WebhookEvent` using explicit
event type fields plus fallback heuristics.

Return type: `WebhookEvent`.

Minimal example:

```python
from erlc_api.webhooks import decode_event_webhook_payload

event = decode_event_webhook_payload(payload, command_prefix=";")
print(event.event_type)
```

Common mistakes:

- Assuming a fixed PRC payload shape. The decoder preserves `event.raw`.

## Event Types And Models

### `WebhookEventType`

Values:

| Value | Meaning |
| --- | --- |
| `WebhookEventType.CUSTOM_COMMAND` | Payload looks like a custom command. |
| `WebhookEventType.EMERGENCY_CALL` | Payload looks like an emergency call. |
| `WebhookEventType.UNKNOWN` | Payload could not be classified. |

### `WebhookSignatureHeaders`

Fields:

| Field | Type |
| --- | --- |
| `timestamp` | `str` |
| `signature_hex` | `str` |

### `CustomCommandInvocation`

Fields:

| Field | Type |
| --- | --- |
| `raw_text` | `str` |
| `prefix` | `str` |
| `command_name` | `str` |
| `args` | `tuple[str, ...]` |
| `command_text` | `str` |

Helper:

| Helper | Return type | Purpose |
| --- | --- | --- |
| `.command_key` | `str` | Lowercase command name for routing. |

### `WebhookEvent`

Fields:

| Field | Type |
| --- | --- |
| `event_type` | `WebhookEventType` |
| `raw` | `Mapping[str, Any]` |
| `event_name` | `str | None` |
| `command` | `CustomCommandInvocation | None` |
| `emergency_call` | `Mapping[str, Any] | None` |

## EventWebhookRouter

Signature:

```python
EventWebhookRouter(
    *,
    command_prefix: str = ";",
    case_sensitive_commands: bool = False,
    raise_on_unsupported: bool = False,
)
```

Purpose: dispatch decoded webhook events to sync or async handlers.

Methods:

| Method | Return type | Purpose |
| --- | --- | --- |
| `on_command(name, handler=None)` | router or decorator | Register custom command handler. |
| `on_emergency_call(handler=None)` | router or decorator | Register emergency call handler. |
| `on_unknown(handler=None)` | router or decorator | Register fallback handler. |
| `decode(payload)` | `WebhookEvent` | Decode payload with router prefix. |
| `dispatch(payload_or_event)` | `list[Any]` | Dispatch to matching handlers. |

Minimal example:

```python
from erlc_api.webhooks import EventWebhookRouter

router = EventWebhookRouter(command_prefix=";")


@router.on_command("ping")
def ping(command, event):
    return {"reply": "pong", "args": list(command.args)}


@router.on_emergency_call()
async def emergency(event):
    return {"call": event.emergency_call}


@router.on_unknown()
def unknown(event):
    return {"ignored": event.event_type}


results = await router.dispatch(payload)
```

Important options:

- `case_sensitive_commands=True` keeps command handler names case-sensitive.
- `raise_on_unsupported=True` raises `UnsupportedWebhookEventError` when no
  handler matches and no unknown handler is registered.
- Handlers may be sync functions or async functions.

Common mistakes:

- Forgetting parentheses on `@router.on_emergency_call()` and `@router.on_unknown()`.
- Registering `ping` but using a different `command_prefix` than the server sends.

## FastAPI Example

```python
from fastapi import FastAPI, HTTPException, Request
from erlc_api.webhooks import EventWebhookRouter, WebhookError, assert_valid_event_webhook_signature

app = FastAPI()
router = EventWebhookRouter(command_prefix=";")


@router.on_command("ping")
def ping(command, event):
    return {"reply": "pong"}


@app.post("/erlc/events")
async def erlc_events(request: Request):
    raw_body = await request.body()
    try:
        assert_valid_event_webhook_signature(raw_body=raw_body, headers=request.headers)
    except WebhookError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    payload = await request.json()
    return {"results": await router.dispatch(payload)}
```

## Webhook Errors

| Exception | Raised when |
| --- | --- |
| `WebhookError` | Base webhook error. |
| `MissingWebhookHeaderError` | Required signature header is missing. |
| `InvalidWebhookSignatureError` | Timestamp, public key, hex signature, or Ed25519 verification fails. |
| `UnsupportedWebhookEventError` | Router cannot dispatch and `raise_on_unsupported=True`. |
