from __future__ import annotations

from dataclasses import dataclass, field
import inspect
from typing import Any, Awaitable, Callable, Mapping

from .webhooks import CustomCommandInvocation, WebhookEvent, decode_event_webhook_payload, parse_custom_command_text


CommandPredicate = Callable[[CustomCommandInvocation, "CustomCommandContext"], bool | Awaitable[bool]]
CommandHandler = Callable[["CustomCommandContext"], Any | Awaitable[Any]]
Middleware = Callable[["CustomCommandContext"], Any | Awaitable[Any]]


@dataclass(frozen=True)
class CustomCommandResponse:
    """Small framework-neutral response for custom command handlers."""

    content: str | None = None
    data: Mapping[str, Any] = field(default_factory=dict)
    ephemeral: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "data": dict(self.data),
            "ephemeral": self.ephemeral,
        }


@dataclass(frozen=True)
class CustomCommandContext:
    """Handler context for PRC webhook custom commands."""

    invocation: CustomCommandInvocation
    event: WebhookEvent
    raw: Mapping[str, Any]
    params: Mapping[str, str] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.invocation.command_name

    @property
    def key(self) -> str:
        return self.invocation.command_key

    @property
    def args(self) -> tuple[str, ...]:
        return self.invocation.args

    @property
    def text(self) -> str:
        return self.invocation.command_text

    def arg(self, index: int, default: str | None = None) -> str | None:
        try:
            return self.args[index]
        except IndexError:
            return default

    def rest(self, start: int = 0) -> str:
        return " ".join(self.args[start:])

    def reply(
        self,
        content: str | None = None,
        *,
        data: Mapping[str, Any] | None = None,
        ephemeral: bool = False,
        **extra: Any,
    ) -> CustomCommandResponse:
        payload = dict(data or {})
        payload.update(extra)
        return CustomCommandResponse(content=content, data=payload, ephemeral=ephemeral)


@dataclass(frozen=True)
class CustomCommandRoute:
    names: tuple[str, ...]
    handler: CommandHandler
    predicate: CommandPredicate | None = None
    description: str | None = None


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


class CustomCommandRouter:
    """Flexible router for PRC webhook messages that start with a command prefix."""

    def __init__(
        self,
        *,
        prefix: str = ";",
        case_sensitive: bool = False,
        unknown_handler: CommandHandler | None = None,
    ) -> None:
        if not prefix or not prefix.strip():
            raise ValueError("prefix cannot be blank.")
        self.prefix = prefix
        self.case_sensitive = case_sensitive
        self.unknown_handler = unknown_handler
        self._routes: list[CustomCommandRoute] = []
        self._middleware: list[Middleware] = []

    @property
    def routes(self) -> tuple[CustomCommandRoute, ...]:
        return tuple(self._routes)

    def _key(self, value: str) -> str:
        key = value.strip()
        if not key:
            raise ValueError("command names cannot be blank.")
        return key if self.case_sensitive else key.lower()

    def command(
        self,
        *names: str,
        predicate: CommandPredicate | None = None,
        description: str | None = None,
    ) -> Callable[[CommandHandler], CommandHandler]:
        if not names:
            raise ValueError("at least one command name is required.")
        normalized = tuple(self._key(name) for name in names)

        def register(handler: CommandHandler) -> CommandHandler:
            self._routes.append(
                CustomCommandRoute(
                    names=normalized,
                    handler=handler,
                    predicate=predicate,
                    description=description,
                )
            )
            return handler

        return register

    def on_unknown(self, handler: CommandHandler) -> CommandHandler:
        self.unknown_handler = handler
        return handler

    def use(self, middleware: Middleware) -> Middleware:
        self._middleware.append(middleware)
        return middleware

    def parse_text(self, text: str) -> CustomCommandInvocation | None:
        return parse_custom_command_text(text, prefix=self.prefix)

    def decode(self, payload: Mapping[str, Any]) -> WebhookEvent:
        return decode_event_webhook_payload(payload, command_prefix=self.prefix)

    def context(self, payload_or_event: Mapping[str, Any] | WebhookEvent) -> CustomCommandContext | None:
        event = payload_or_event if isinstance(payload_or_event, WebhookEvent) else self.decode(payload_or_event)
        if event.command is None:
            return None
        return CustomCommandContext(invocation=event.command, event=event, raw=event.raw)

    def match(self, context: CustomCommandContext) -> CustomCommandRoute | None:
        key = context.key if not self.case_sensitive else context.name
        for route in self._routes:
            if key not in route.names:
                continue
            if route.predicate is not None:
                allowed = route.predicate(context.invocation, context)
                if inspect.isawaitable(allowed):
                    close = getattr(allowed, "close", None)
                    if callable(close):
                        close()
                    raise TypeError("Async predicates require `await router.dispatch(...)`.")
                if not allowed:
                    continue
            return route
        return None

    async def _match_async(self, context: CustomCommandContext) -> CustomCommandRoute | None:
        key = context.key if not self.case_sensitive else context.name
        for route in self._routes:
            if key not in route.names:
                continue
            if route.predicate is not None and not await _maybe_await(route.predicate(context.invocation, context)):
                continue
            return route
        return None

    async def dispatch(self, payload_or_event: Mapping[str, Any] | WebhookEvent) -> Any:
        context = self.context(payload_or_event)
        if context is None:
            return None

        for middleware in self._middleware:
            result = await _maybe_await(middleware(context))
            if result is not None:
                return result

        route = await self._match_async(context)
        if route is not None:
            return await _maybe_await(route.handler(context))
        if self.unknown_handler is not None:
            return await _maybe_await(self.unknown_handler(context))
        return None

    def help(self) -> list[dict[str, Any]]:
        return [
            {
                "names": list(route.names),
                "description": route.description,
            }
            for route in self._routes
        ]


__all__ = [
    "CommandHandler",
    "CommandPredicate",
    "CustomCommandContext",
    "CustomCommandResponse",
    "CustomCommandRoute",
    "CustomCommandRouter",
    "Middleware",
]
