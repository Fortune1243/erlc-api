# src/erlc_api/helpers.py
from __future__ import annotations
from .client import ERLCClient, ValidationResult
from .context import ERLCContext


async def validate_server_key(client: ERLCClient, ctx: ERLCContext) -> ValidationResult:
    """Backward-compatible helper that delegates to ERLCClient.validate_key."""
    return await client.validate_key(ctx)
