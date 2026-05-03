from __future__ import annotations

import pytest

from erlc_api.custom_commands import CustomCommandResponse, CustomCommandRouter
from erlc_api.webhooks import decode_event_webhook_payload


def test_custom_command_router_parses_text_and_exposes_context() -> None:
    router = CustomCommandRouter(prefix=";")
    invocation = router.parse_text(';note "Player One" hello')

    assert invocation is not None
    assert invocation.command_name == "note"
    assert invocation.args == ("Player One", "hello")

    context = router.context({"Message": ';note "Player One" hello'})
    assert context is not None
    assert context.name == "note"
    assert context.arg(0) == "Player One"
    assert context.arg(99, "missing") == "missing"
    assert context.rest(1) == "hello"
    assert context.reply("ok", data={"source": "test"}, ephemeral=True, target="Player One").to_dict() == {
        "content": "ok",
        "data": {"source": "test", "target": "Player One"},
        "ephemeral": True,
    }


@pytest.mark.asyncio
async def test_custom_command_router_dispatches_aliases_and_async_handlers() -> None:
    router = CustomCommandRouter()

    @router.command("ping", "p", description="Ping command")
    async def ping(context):
        return context.reply("pong", args=list(context.args))

    result = await router.dispatch({"Message": ";p one two"})

    assert isinstance(result, CustomCommandResponse)
    assert result.content == "pong"
    assert result.data == {"args": ["one", "two"]}
    assert router.help() == [{"names": ["ping", "p"], "description": "Ping command"}]


@pytest.mark.asyncio
async def test_custom_command_router_dispatches_sync_handler_from_decoded_event() -> None:
    router = CustomCommandRouter()

    @router.command("echo")
    def echo(context):
        return {"text": context.rest()}

    event = decode_event_webhook_payload({"Type": "CustomCommand", "Message": ";echo hello there"})

    assert await router.dispatch(event) == {"text": "hello there"}


@pytest.mark.asyncio
async def test_custom_command_router_supports_predicates_middleware_and_unknown_handler() -> None:
    router = CustomCommandRouter()

    @router.use
    def block_stop(context):
        if context.name == "stop":
            return {"blocked": True}
        return None

    @router.command("staff", predicate=lambda invocation, context: context.arg(0) == "allow")
    def staff(context):
        return {"ok": True}

    @router.on_unknown
    def unknown(context):
        return {"unknown": context.name}

    assert await router.dispatch({"Message": ";stop"}) == {"blocked": True}
    assert await router.dispatch({"Message": ";staff allow"}) == {"ok": True}
    assert await router.dispatch({"Message": ";staff deny"}) == {"unknown": "staff"}
    assert await router.dispatch({"Message": "regular chat"}) is None


@pytest.mark.asyncio
async def test_custom_command_router_supports_async_predicates() -> None:
    router = CustomCommandRouter()

    async def allowed(_invocation, context):
        return context.arg(0) == "yes"

    @router.command("gate", predicate=allowed)
    def gate(context):
        return {"allowed": True}

    assert await router.dispatch({"Message": ";gate yes"}) == {"allowed": True}
    assert await router.dispatch({"Message": ";gate no"}) is None
    context = router.context({"Message": ";gate yes"})
    assert context is not None
    with pytest.raises(TypeError, match="Async predicates"):
        router.match(context)


def test_custom_command_router_validates_names_and_prefix() -> None:
    with pytest.raises(ValueError, match="prefix"):
        CustomCommandRouter(prefix="")
    with pytest.raises(ValueError, match="prefix"):
        CustomCommandRouter(prefix=" ")

    router = CustomCommandRouter()
    with pytest.raises(ValueError, match="at least one"):
        router.command()
    with pytest.raises(ValueError, match="blank"):
        router.command(" ")
