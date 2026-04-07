import pytest
from erlc_api import ERLCClient, ValidationStatus
from erlc_api._errors import APIError, AuthError, NetworkError, RateLimitError


@pytest.mark.asyncio
async def test_client_init() -> None:
    api = ERLCClient()
    assert api is not None


@pytest.mark.asyncio
async def test_validate_key_ok() -> None:
    api = ERLCClient()
    ctx = api.ctx("abcd1234")

    async def fake_server(_ctx):
        return {"ok": True}

    api.v1.server = fake_server  # type: ignore[method-assign]
    result = await api.validate_key(ctx)
    assert result.status == ValidationStatus.OK


@pytest.mark.asyncio
async def test_validate_key_auth_error() -> None:
    api = ERLCClient()
    ctx = api.ctx("abcd1234")

    async def fake_server(_ctx):
        raise AuthError("bad auth", method="GET", path="/v1/server", status=401)

    api.v1.server = fake_server  # type: ignore[method-assign]
    result = await api.validate_key(ctx)
    assert result.status == ValidationStatus.AUTH_ERROR


@pytest.mark.asyncio
async def test_validate_key_rate_limited() -> None:
    api = ERLCClient()
    ctx = api.ctx("abcd1234")

    async def fake_server(_ctx):
        raise RateLimitError(
            "slow down",
            method="GET",
            path="/v1/server",
            status=429,
            retry_after=2.5,
        )

    api.v1.server = fake_server  # type: ignore[method-assign]
    result = await api.validate_key(ctx)
    assert result.status == ValidationStatus.RATE_LIMITED
    assert result.retry_after == 2.5


@pytest.mark.asyncio
async def test_validate_key_network_error() -> None:
    api = ERLCClient()
    ctx = api.ctx("abcd1234")

    async def fake_server(_ctx):
        raise NetworkError("network", method="GET", path="/v1/server")

    api.v1.server = fake_server  # type: ignore[method-assign]
    result = await api.validate_key(ctx)
    assert result.status == ValidationStatus.NETWORK_ERROR


@pytest.mark.asyncio
async def test_validate_key_api_error() -> None:
    api = ERLCClient()
    ctx = api.ctx("abcd1234")

    async def fake_server(_ctx):
        raise APIError("api", method="GET", path="/v1/server", status=500)

    api.v1.server = fake_server  # type: ignore[method-assign]
    result = await api.validate_key(ctx)
    assert result.status == ValidationStatus.API_ERROR
    assert result.api_status == 500


@pytest.mark.asyncio
async def test_validate_key_blank_key_raises() -> None:
    api = ERLCClient()
    with pytest.raises(ValueError):
        await api.validate_key(api.ctx("   "))


@pytest.mark.asyncio
async def test_v1_command_rejects_log_command_without_request() -> None:
    api = ERLCClient()
    ctx = api.ctx("abcd1234")
    called = False

    async def fake_request(*_args, **_kwargs):
        nonlocal called
        called = True
        return {"ok": True}

    api.v1._request = fake_request  # type: ignore[method-assign]

    with pytest.raises(ValueError, match=":log"):
        await api.v1.command(ctx, "  :LoG incident external-review-started")

    assert called is False


@pytest.mark.asyncio
async def test_v1_command_allows_non_log_command() -> None:
    api = ERLCClient()
    ctx = api.ctx("abcd1234")
    seen: dict[str, object] = {}

    async def fake_request(*args, **kwargs):
        seen["args"] = args
        seen["kwargs"] = kwargs
        return {"ok": True}

    api.v1._request = fake_request  # type: ignore[method-assign]

    result = await api.v1.command(ctx, ":help")

    assert result == {"ok": True}
    assert seen["args"] == (ctx, "POST", "/v1/server/command")
    assert seen["kwargs"] == {
        "path_template": "/v1/server/command",
        "json": {"command": ":help"},
        "idempotent": False,
    }
