from __future__ import annotations

import pytest

from erlc_api.webhooks import (
    CustomCommandInvocation,
    EventWebhookRouter,
    InvalidWebhookSignatureError,
    MissingWebhookHeaderError,
    UnsupportedWebhookEventError,
    WebhookEventType,
    assert_valid_event_webhook_signature,
    decode_event_webhook_payload,
    parse_custom_command_text,
    verify_event_webhook_signature,
)


def _signed_headers(*, timestamp: str = "1700000000", signature_hex: str = "00") -> dict[str, str]:
    return {
        "X-Signature-Timestamp": timestamp,
        "X-Signature-Ed25519": signature_hex,
    }


def test_assert_valid_event_webhook_signature_missing_headers_raises() -> None:
    with pytest.raises(MissingWebhookHeaderError):
        assert_valid_event_webhook_signature(raw_body=b"{}", headers={})


def test_assert_valid_event_webhook_signature_bad_hex_raises() -> None:
    with pytest.raises(InvalidWebhookSignatureError):
        assert_valid_event_webhook_signature(
            raw_body=b"{}",
            headers=_signed_headers(signature_hex="zz"),
            max_skew_s=None,
        )


def test_assert_valid_event_webhook_signature_fails_when_timestamp_skew_exceeded() -> None:
    with pytest.raises(InvalidWebhookSignatureError):
        assert_valid_event_webhook_signature(
            raw_body=b"{}",
            headers=_signed_headers(timestamp="100"),
            now_epoch_s=1000,
            max_skew_s=10,
        )


def test_assert_valid_event_webhook_signature_builds_message_as_timestamp_plus_raw_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, bytes] = {}

    class FakeVerifier:
        def verify(self, signature: bytes, message: bytes) -> None:
            captured["signature"] = signature
            captured["message"] = message

    monkeypatch.setattr("erlc_api.webhooks._load_public_key", lambda _public_key: FakeVerifier())

    assert_valid_event_webhook_signature(
        raw_body=b'{"hello":"world"}',
        headers=_signed_headers(timestamp="1700000001", signature_hex="0a0b"),
        max_skew_s=None,
    )

    assert captured["signature"] == bytes.fromhex("0a0b")
    assert captured["message"] == b"1700000001" + b'{"hello":"world"}'


def test_assert_valid_event_webhook_signature_invalid_signature_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeVerifier:
        def verify(self, signature: bytes, message: bytes) -> None:  # pragma: no cover - signature path only
            raise ValueError("bad signature")

    monkeypatch.setattr("erlc_api.webhooks._load_public_key", lambda _public_key: FakeVerifier())

    with pytest.raises(InvalidWebhookSignatureError):
        assert_valid_event_webhook_signature(
            raw_body=b"{}",
            headers=_signed_headers(),
            max_skew_s=None,
        )


def test_verify_event_webhook_signature_returns_false_for_invalid_cases() -> None:
    assert verify_event_webhook_signature(raw_body=b"{}", headers={}) is False


def test_parse_custom_command_text_supports_quotes() -> None:
    parsed = parse_custom_command_text(';ban "Player One" rdm')

    assert parsed == CustomCommandInvocation(
        raw_text=';ban "Player One" rdm',
        prefix=";",
        command_name="ban",
        args=("Player One", "rdm"),
        command_text='ban "Player One" rdm',
    )


def test_parse_custom_command_text_returns_none_for_non_command() -> None:
    assert parse_custom_command_text("hello world") is None
    assert parse_custom_command_text(";") is None


def test_decode_event_webhook_payload_prefers_explicit_type_for_custom_command() -> None:
    event = decode_event_webhook_payload({"Type": "CustomCommand", "Message": ";ping now"})

    assert event.event_type is WebhookEventType.CUSTOM_COMMAND
    assert event.command is not None
    assert event.command.command_name == "ping"
    assert event.command.args == ("now",)


def test_decode_event_webhook_payload_emergency_call_heuristics_without_type() -> None:
    event = decode_event_webhook_payload({"Team": "Fire", "Caller": 12345, "Position": [1.0, 2.0], "StartedAt": 100})

    assert event.event_type is WebhookEventType.EMERGENCY_CALL
    assert event.emergency_call is not None
    assert event.emergency_call["Team"] == "Fire"


def test_decode_event_webhook_payload_unknown_when_no_supported_shape() -> None:
    event = decode_event_webhook_payload({"hello": "world"})
    assert event.event_type is WebhookEventType.UNKNOWN
    assert event.command is None
    assert event.emergency_call is None


@pytest.mark.asyncio
async def test_router_dispatches_sync_and_async_command_handlers() -> None:
    router = EventWebhookRouter()
    calls: list[str] = []

    def ping_handler(invocation, event) -> str:
        calls.append(f"sync:{invocation.command_name}")
        return "pong"

    async def echo_handler(invocation, event) -> str:
        calls.append(f"async:{invocation.command_name}")
        return "ok"

    router.on_command("ping", ping_handler)
    router.on_command("echo", echo_handler)

    ping_result = await router.dispatch({"Message": ";ping one"})
    echo_result = await router.dispatch({"Message": ";echo two"})

    assert ping_result == ["pong"]
    assert echo_result == ["ok"]
    assert calls == ["sync:ping", "async:echo"]


@pytest.mark.asyncio
async def test_router_dispatches_emergency_handlers_in_order() -> None:
    router = EventWebhookRouter()
    calls: list[str] = []

    def first(event) -> str:
        calls.append("first")
        return "a"

    async def second(event) -> str:
        calls.append("second")
        return "b"

    router.on_emergency_call(first)
    router.on_emergency_call(second)

    result = await router.dispatch({"Type": "EmergencyCall", "Data": {"Team": "DOT", "Caller": 1, "Position": [0, 1]}})

    assert result == ["a", "b"]
    assert calls == ["first", "second"]


@pytest.mark.asyncio
async def test_router_uses_unknown_handler_for_unregistered_command() -> None:
    router = EventWebhookRouter()

    def unknown_handler(event) -> str:
        return f"unknown:{event.event_type}"

    router.on_unknown(unknown_handler)
    result = await router.dispatch({"Message": ";not_registered hi"})

    assert result == ["unknown:custom_command"]


@pytest.mark.asyncio
async def test_router_raise_on_unsupported_when_no_handlers() -> None:
    router = EventWebhookRouter(raise_on_unsupported=True)

    with pytest.raises(UnsupportedWebhookEventError):
        await router.dispatch({"hello": "world"})
