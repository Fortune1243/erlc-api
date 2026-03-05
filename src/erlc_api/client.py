# src/erlc_api/client.py
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping, Optional

from .context import ERLCContext
from ._errors import APIError, AuthError, NetworkError, RateLimitError
from ._http import AsyncHTTP, ClientConfig
from ._ratelimit import RateLimiter
from .v1 import V1
from .v2 import V2


class ValidationStatus(StrEnum):
    OK = "ok"
    AUTH_ERROR = "auth_error"
    RATE_LIMITED = "rate_limited"
    NETWORK_ERROR = "network_error"
    API_ERROR = "api_error"


@dataclass(frozen=True)
class ValidationResult:
    status: ValidationStatus
    retry_after: float | None = None
    api_status: int | None = None


@dataclass
class ERLCClient:
    config: ClientConfig = field(default_factory=ClientConfig)

    def __post_init__(self) -> None:
        self._limiter = RateLimiter()
        self._http = AsyncHTTP(self.config, self._limiter)
        self.v1 = V1(self._request)
        self.v2 = V2(self._request)

    async def start(self) -> None:
        await self._http.start()

    async def close(self) -> None:
        await self._http.close()

    def ctx(self, server_key: str) -> ERLCContext:
        # Convenience factory
        return ERLCContext(server_key=server_key.strip())

    async def validate_key(self, ctx: ERLCContext) -> ValidationResult:
        """
        Validate a server key using a lightweight authenticated endpoint.

        Expected API failures are returned as structured statuses so setup flows
        can branch without exception handling.
        """
        if not ctx.server_key.strip():
            raise ValueError("Context must include a non-empty server key.")

        try:
            await self.v1.server(ctx)
            return ValidationResult(status=ValidationStatus.OK)
        except AuthError:
            return ValidationResult(status=ValidationStatus.AUTH_ERROR)
        except RateLimitError as exc:
            return ValidationResult(status=ValidationStatus.RATE_LIMITED, retry_after=exc.retry_after)
        except NetworkError:
            return ValidationResult(status=ValidationStatus.NETWORK_ERROR)
        except APIError as exc:
            return ValidationResult(status=ValidationStatus.API_ERROR, api_status=exc.status)

    async def _request(
        self,
        ctx: ERLCContext,
        method: str,
        path: str,
        *,
        path_template: Optional[str] = None,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        idempotent: bool = True,
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> Any:
        headers = {"Server-Key": ctx.server_key}
        if extra_headers:
            # Ensure Server-Key cannot be overwritten by mistake
            for k, v in extra_headers.items():
                if k.lower() == "server-key":
                    continue
                headers[k] = v

        return await self._http.request(
            key_id=ctx.key_id,
            method=method,
            path=path,
            path_template=path_template,
            headers=headers,
            params=params,
            json=json,
            idempotent=idempotent,
        )
