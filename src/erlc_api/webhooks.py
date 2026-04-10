from __future__ import annotations

import base64
from dataclasses import dataclass, field
from enum import StrEnum
from functools import lru_cache
import inspect
import shlex
import time
from typing import Any, Awaitable, Callable, Mapping, Sequence

PRC_EVENT_WEBHOOK_PUBLIC_KEY_SPKI_B64 = "MCowBQYDK2VwAyEAjSICb9pp0kHizGQtdG8ySWsDChfGqi+gyFCttigBNOA="


class WebhookError(Exception):
    """Base exception for webhook parsing or verification failures."""


class MissingWebhookHeaderError(WebhookError):
    """Required webhook signature headers are missing."""


class InvalidWebhookSignatureError(WebhookError):
    """Webhook signature did not pass validation checks."""


class UnsupportedWebhookEventError(WebhookError):
    """Webhook event could not be handled by the configured router."""


class WebhookEventType(StrEnum):
    CUSTOM_COMMAND = "custom_command"
    EMERGENCY_CALL = "emergency_call"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class WebhookSignatureHeaders:
    timestamp: str
    signature_hex: str


@dataclass(frozen=True)
class CustomCommandInvocation:
    raw_text: str
    prefix: str
    command_name: str
    args: tuple[str, ...] = field(default_factory=tuple)
    command_text: str = ""

    @property
    def command_key(self) -> str:
        return self.command_name.lower()


@dataclass(frozen=True)
class WebhookEvent:
    event_type: WebhookEventType
    raw: Mapping[str, Any]
    event_name: str | None = None
    command: CustomCommandInvocation | None = None
    emergency_call: Mapping[str, Any] | None = None


CommandHandler = Callable[[CustomCommandInvocation, WebhookEvent], Any | Awaitable[Any]]
EmergencyCallHandler = Callable[[WebhookEvent], Any | Awaitable[Any]]
UnknownEventHandler = Callable[[WebhookEvent], Any | Awaitable[Any]]


def _header_lookup(headers: Mapping[str, Any], key: str) -> str | None:
    wanted = key.lower()
    for name, value in headers.items():
        if str(name).lower() != wanted:
            continue
        if value is None:
            return None
        text = str(value).strip()
        if text:
            return text
        return None
    return None


def extract_webhook_signature_headers(headers: Mapping[str, Any]) -> WebhookSignatureHeaders:
    """Extract and validate the two webhook signature headers from a mapping."""
    timestamp = _header_lookup(headers, "X-Signature-Timestamp")
    signature_hex = _header_lookup(headers, "X-Signature-Ed25519")

    missing: list[str] = []
    if not timestamp:
        missing.append("X-Signature-Timestamp")
    if not signature_hex:
        missing.append("X-Signature-Ed25519")
    if missing:
        raise MissingWebhookHeaderError(f"Missing required webhook header(s): {', '.join(missing)}.")

    return WebhookSignatureHeaders(timestamp=timestamp, signature_hex=signature_hex)


def _normalize_body(raw_body: bytes | bytearray | memoryview) -> bytes:
    if isinstance(raw_body, bytes):
        return raw_body
    if isinstance(raw_body, bytearray):
        return bytes(raw_body)
    if isinstance(raw_body, memoryview):
        return raw_body.tobytes()
    raise TypeError("raw_body must be bytes-like (bytes/bytearray/memoryview).")


@lru_cache(maxsize=8)
def _load_public_key(public_key_b64: str) -> Any:
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "Event webhook signature verification requires `cryptography`. Install with `pip install erlc-api[webhooks]`."
        ) from exc

    try:
        der = base64.b64decode(public_key_b64, validate=True)
    except Exception as exc:
        raise InvalidWebhookSignatureError("Webhook public key must be valid base64-encoded DER (SPKI).") from exc

    try:
        key = serialization.load_der_public_key(der)
    except Exception as exc:
        raise InvalidWebhookSignatureError("Webhook public key is not a valid DER/SPKI public key.") from exc

    if not isinstance(key, Ed25519PublicKey):
        raise InvalidWebhookSignatureError("Webhook public key must be an Ed25519 SPKI public key.")
    return key


def assert_valid_event_webhook_signature(
    *,
    raw_body: bytes | bytearray | memoryview,
    headers: Mapping[str, Any] | WebhookSignatureHeaders,
    public_key_b64: str = PRC_EVENT_WEBHOOK_PUBLIC_KEY_SPKI_B64,
    max_skew_s: float | None = 300,
    now_epoch_s: float | None = None,
) -> None:
    """
    Validate PRC event webhook signature and raise on any validation failure.

    Signature input is `timestamp + raw_body` where `timestamp` is UTF-8 bytes.
    """
    parsed_headers = headers if isinstance(headers, WebhookSignatureHeaders) else extract_webhook_signature_headers(headers)

    if max_skew_s is not None:
        try:
            timestamp_int = int(parsed_headers.timestamp)
        except ValueError as exc:
            raise InvalidWebhookSignatureError("X-Signature-Timestamp must be a valid Unix timestamp string.") from exc

        now = time.time() if now_epoch_s is None else now_epoch_s
        if abs(now - timestamp_int) > max_skew_s:
            raise InvalidWebhookSignatureError(
                f"Webhook timestamp is outside allowed skew window (max_skew_s={max_skew_s})."
            )

    try:
        signature = bytes.fromhex(parsed_headers.signature_hex)
    except ValueError as exc:
        raise InvalidWebhookSignatureError("X-Signature-Ed25519 must be a valid hex string.") from exc

    message = parsed_headers.timestamp.encode("utf-8") + _normalize_body(raw_body)
    verifier = _load_public_key(public_key_b64)
    try:
        verifier.verify(signature, message)
    except Exception as exc:
        raise InvalidWebhookSignatureError("Webhook Ed25519 signature verification failed.") from exc


def verify_event_webhook_signature(
    *,
    raw_body: bytes | bytearray | memoryview,
    headers: Mapping[str, Any] | WebhookSignatureHeaders,
    public_key_b64: str = PRC_EVENT_WEBHOOK_PUBLIC_KEY_SPKI_B64,
    max_skew_s: float | None = 300,
    now_epoch_s: float | None = None,
) -> bool:
    """Return `True` when webhook signature verifies, `False` when it does not."""
    try:
        assert_valid_event_webhook_signature(
            raw_body=raw_body,
            headers=headers,
            public_key_b64=public_key_b64,
            max_skew_s=max_skew_s,
            now_epoch_s=now_epoch_s,
        )
    except WebhookError:
        return False
    return True


def parse_custom_command_text(text: str, *, prefix: str = ";") -> CustomCommandInvocation | None:
    """Parse a custom command message starting with a prefix (default `;`)."""
    if not isinstance(text, str):
        return None
    cleaned = text.strip()
    if not cleaned.startswith(prefix):
        return None

    command_text = cleaned[len(prefix) :].strip()
    if not command_text:
        return None

    try:
        tokens = shlex.split(command_text, posix=True)
    except ValueError:
        tokens = command_text.split()
    if not tokens:
        return None

    return CustomCommandInvocation(
        raw_text=text,
        prefix=prefix,
        command_name=tokens[0],
        args=tuple(tokens[1:]),
        command_text=command_text,
    )


def _candidate_mappings(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    out: list[Mapping[str, Any]] = [payload]
    for key in ("Data", "data", "Payload", "payload", "Event", "event"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            out.append(value)
    return out


def _first_string(payloads: Sequence[Mapping[str, Any]], keys: Sequence[str]) -> str | None:
    for payload in payloads:
        for key in keys:
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _normalize_event_name(value: str | None) -> str:
    if value is None:
        return ""
    return value.lower().replace("_", "").replace("-", "").replace(" ", "")


def _infer_event_type(explicit_name: str | None, *, command: CustomCommandInvocation | None, emergency: Mapping[str, Any] | None) -> WebhookEventType:
    normalized = _normalize_event_name(explicit_name)
    if "emergency" in normalized:
        return WebhookEventType.EMERGENCY_CALL
    if "command" in normalized or "chat" in normalized or "message" in normalized:
        return WebhookEventType.CUSTOM_COMMAND
    if command is not None:
        return WebhookEventType.CUSTOM_COMMAND
    if emergency is not None:
        return WebhookEventType.EMERGENCY_CALL
    return WebhookEventType.UNKNOWN


def _looks_like_emergency_call(payload: Mapping[str, Any]) -> bool:
    lowered = {str(key).lower().replace("_", "") for key in payload.keys()}
    has_team = "team" in lowered
    has_caller = "caller" in lowered or "players" in lowered
    has_position_or_time = "position" in lowered or "startedat" in lowered or "callnumber" in lowered
    return has_team and has_caller and has_position_or_time


def _find_emergency_call_payload(payloads: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    for payload in payloads:
        for key in ("EmergencyCall", "emergencyCall", "emergency_call", "Emergency", "emergency"):
            value = payload.get(key)
            if isinstance(value, Mapping):
                return dict(value)
    for payload in payloads:
        if _looks_like_emergency_call(payload):
            return dict(payload)
    return None


def decode_event_webhook_payload(payload: Mapping[str, Any], *, command_prefix: str = ";") -> WebhookEvent:
    """
    Decode a raw webhook payload into a typed event with resilient fallback heuristics.

    Explicit event-name fields are preferred when present:
    `Type`, `type`, `EventType`, `eventType`.
    """
    if not isinstance(payload, Mapping):
        raise TypeError("payload must be a mapping/object.")

    raw = dict(payload)
    candidates = _candidate_mappings(raw)
    explicit_type = _first_string(candidates, ("Type", "type", "EventType", "eventType"))

    command_text = _first_string(
        candidates,
        ("Command", "command", "Message", "message", "Content", "content", "Text", "text", "ChatMessage", "chatMessage"),
    )
    command = parse_custom_command_text(command_text, prefix=command_prefix) if command_text is not None else None
    emergency_call = _find_emergency_call_payload(candidates)

    return WebhookEvent(
        event_type=_infer_event_type(explicit_type, command=command, emergency=emergency_call),
        raw=raw,
        event_name=explicit_type,
        command=command,
        emergency_call=emergency_call,
    )


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


class EventWebhookRouter:
    """
    Lightweight event router for PRC webhook payloads.

    Supports both sync and async handlers for command, emergency-call, and
    unknown-event paths.
    """

    def __init__(
        self,
        *,
        command_prefix: str = ";",
        case_sensitive_commands: bool = False,
        raise_on_unsupported: bool = False,
    ) -> None:
        self.command_prefix = command_prefix
        self.case_sensitive_commands = case_sensitive_commands
        self.raise_on_unsupported = raise_on_unsupported
        self._command_handlers: dict[str, CommandHandler] = {}
        self._emergency_handlers: list[EmergencyCallHandler] = []
        self._unknown_handler: UnknownEventHandler | None = None

    def _command_key(self, name: str) -> str:
        return name if self.case_sensitive_commands else name.lower()

    def on_command(self, name: str, handler: CommandHandler | None = None) -> EventWebhookRouter | Callable[[CommandHandler], CommandHandler]:
        """Register a command handler (or use as decorator)."""
        key = self._command_key(name.strip())
        if not key:
            raise ValueError("Command handler name cannot be blank.")

        def register(func: CommandHandler) -> CommandHandler:
            self._command_handlers[key] = func
            return func

        if handler is not None:
            register(handler)
            return self
        return register

    def on_emergency_call(
        self,
        handler: EmergencyCallHandler | None = None,
    ) -> EventWebhookRouter | Callable[[EmergencyCallHandler], EmergencyCallHandler]:
        """Register an emergency call handler (or use as decorator)."""

        def register(func: EmergencyCallHandler) -> EmergencyCallHandler:
            self._emergency_handlers.append(func)
            return func

        if handler is not None:
            register(handler)
            return self
        return register

    def on_unknown(
        self,
        handler: UnknownEventHandler | None = None,
    ) -> EventWebhookRouter | Callable[[UnknownEventHandler], UnknownEventHandler]:
        """Register a fallback handler for unknown/unhandled events."""

        def register(func: UnknownEventHandler) -> UnknownEventHandler:
            self._unknown_handler = func
            return func

        if handler is not None:
            register(handler)
            return self
        return register

    def decode(self, payload: Mapping[str, Any]) -> WebhookEvent:
        """Decode a payload using this router's configured command prefix."""
        return decode_event_webhook_payload(payload, command_prefix=self.command_prefix)

    async def dispatch(self, payload_or_event: Mapping[str, Any] | WebhookEvent) -> list[Any]:
        """Decode and dispatch an event to matching handlers."""
        event = payload_or_event if isinstance(payload_or_event, WebhookEvent) else self.decode(payload_or_event)

        if event.event_type is WebhookEventType.CUSTOM_COMMAND and event.command is not None:
            handler = self._command_handlers.get(self._command_key(event.command.command_name))
            if handler is not None:
                return [await _maybe_await(handler(event.command, event))]
            return await self._dispatch_unknown(event, f"No handler registered for command '{event.command.command_name}'.")

        if event.event_type is WebhookEventType.EMERGENCY_CALL:
            if self._emergency_handlers:
                out: list[Any] = []
                for handler in self._emergency_handlers:
                    out.append(await _maybe_await(handler(event)))
                return out
            return await self._dispatch_unknown(event, "No emergency call handlers registered.")

        return await self._dispatch_unknown(event, "Webhook event is unknown or unsupported.")

    async def _dispatch_unknown(self, event: WebhookEvent, message: str) -> list[Any]:
        if self._unknown_handler is not None:
            return [await _maybe_await(self._unknown_handler(event))]
        if self.raise_on_unsupported:
            raise UnsupportedWebhookEventError(message)
        return []


__all__ = [
    "PRC_EVENT_WEBHOOK_PUBLIC_KEY_SPKI_B64",
    "CustomCommandInvocation",
    "EventWebhookRouter",
    "InvalidWebhookSignatureError",
    "MissingWebhookHeaderError",
    "UnsupportedWebhookEventError",
    "WebhookError",
    "WebhookEvent",
    "WebhookEventType",
    "WebhookSignatureHeaders",
    "assert_valid_event_webhook_signature",
    "decode_event_webhook_payload",
    "extract_webhook_signature_headers",
    "parse_custom_command_text",
    "verify_event_webhook_signature",
]
