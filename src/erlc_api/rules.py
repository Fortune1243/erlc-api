from __future__ import annotations

from dataclasses import dataclass, field
import inspect
import time
from typing import Any, Awaitable, Callable, Mapping

from . import _utility as u


RulePredicate = Callable[["RuleContext"], bool | str | Mapping[str, Any] | "RuleMatch" | None | Awaitable[Any]]
RuleCallback = Callable[["RuleMatch"], Any | Awaitable[Any]]


_SEVERITY_RANK = {"ok": 0, "info": 1, "warning": 2, "error": 3, "critical": 4}


@dataclass(frozen=True)
class RuleContext:
    data: Any
    previous: Any = None
    event: Any = None
    now: float = field(default_factory=time.time)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RuleMatch:
    rule_name: str
    severity: str = "info"
    message: str | None = None
    data: Any = None
    context: RuleContext | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "severity": self.severity,
            "message": self.message,
            "data": u.model_dict(self.data),
            "metadata": dict(self.context.metadata) if self.context is not None else {},
        }


@dataclass(frozen=True)
class Rule:
    name: str
    predicate: RulePredicate
    severity: str = "info"
    message: str | None = None
    callback: RuleCallback | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("rule name cannot be blank.")
        if self.severity not in _SEVERITY_RANK:
            raise ValueError("severity must be one of ok, info, warning, error, critical.")

    def _match_from_result(self, result: Any, context: RuleContext) -> RuleMatch | None:
        if result is None or result is False:
            return None
        if isinstance(result, RuleMatch):
            return result
        if isinstance(result, Mapping):
            return RuleMatch(
                rule_name=str(result.get("rule_name", self.name)),
                severity=str(result.get("severity", self.severity)),
                message=result.get("message", self.message),
                data=result.get("data", context.data),
                context=context,
            )
        return RuleMatch(
            rule_name=self.name,
            severity=self.severity,
            message=str(result) if isinstance(result, str) else self.message,
            data=context.data,
            context=context,
        )

    def evaluate(self, context: RuleContext) -> RuleMatch | None:
        result = self.predicate(context)
        if inspect.isawaitable(result):
            close = getattr(result, "close", None)
            if callable(close):
                close()
            raise TypeError("Async predicates require `await AsyncRuleEngine.evaluate(...)`.")
        return self._match_from_result(result, context)

    async def evaluate_async(self, context: RuleContext) -> RuleMatch | None:
        result = self.predicate(context)
        if inspect.isawaitable(result):
            result = await result
        return self._match_from_result(result, context)


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


class RuleEngine:
    def __init__(self, rules: list[Rule] | None = None) -> None:
        self.rules = list(rules or [])

    def add(
        self,
        name: str,
        predicate: RulePredicate,
        *,
        severity: str = "info",
        message: str | None = None,
        callback: RuleCallback | None = None,
        tags: tuple[str, ...] = (),
    ) -> Rule:
        rule = Rule(name=name, predicate=predicate, severity=severity, message=message, callback=callback, tags=tags)
        self.rules.append(rule)
        return rule

    def evaluate(self, data: Any, *, previous: Any = None, event: Any = None, metadata: Mapping[str, Any] | None = None) -> list[RuleMatch]:
        context = RuleContext(data=data, previous=previous, event=event, metadata=dict(metadata or {}))
        matches: list[RuleMatch] = []
        for rule in self.rules:
            match = rule.evaluate(context)
            if match is None:
                continue
            matches.append(match)
            if rule.callback is not None:
                result = rule.callback(match)
                if inspect.isawaitable(result):
                    close = getattr(result, "close", None)
                    if callable(close):
                        close()
                    raise TypeError("Async callbacks require `await AsyncRuleEngine.evaluate(...)`.")
        return matches


class AsyncRuleEngine:
    def __init__(self, rules: list[Rule] | None = None) -> None:
        self.rules = list(rules or [])

    def add(
        self,
        name: str,
        predicate: RulePredicate,
        *,
        severity: str = "info",
        message: str | None = None,
        callback: RuleCallback | None = None,
        tags: tuple[str, ...] = (),
    ) -> Rule:
        rule = Rule(name=name, predicate=predicate, severity=severity, message=message, callback=callback, tags=tags)
        self.rules.append(rule)
        return rule

    async def evaluate(self, data: Any, *, previous: Any = None, event: Any = None, metadata: Mapping[str, Any] | None = None) -> list[RuleMatch]:
        context = RuleContext(data=data, previous=previous, event=event, metadata=dict(metadata or {}))
        matches: list[RuleMatch] = []
        for rule in self.rules:
            match = await rule.evaluate_async(context)
            if match is None:
                continue
            matches.append(match)
            if rule.callback is not None:
                await _maybe_await(rule.callback(match))
        return matches


def _count(value: list[Any], fallback: int | None = None) -> int:
    return len(value) if value else int(fallback or 0)


def _passes(count: int, *, equals: int | None = None, at_least: int | None = None, at_most: int | None = None) -> bool:
    return (equals is None or count == equals) and (at_least is None or count >= at_least) and (at_most is None or count <= at_most)


class Conditions:
    @staticmethod
    def player_count(*, equals: int | None = None, at_least: int | None = None, at_most: int | None = None) -> RulePredicate:
        def predicate(context: RuleContext) -> bool:
            fallback = getattr(context.data, "current_players", None)
            return _passes(_count(u.players(context.data), fallback), equals=equals, at_least=at_least, at_most=at_most)

        return predicate

    @staticmethod
    def queue_length(*, equals: int | None = None, at_least: int | None = None, at_most: int | None = None) -> RulePredicate:
        def predicate(context: RuleContext) -> bool:
            return _passes(len(u.queue(context.data)), equals=equals, at_least=at_least, at_most=at_most)

        return predicate

    @staticmethod
    def staff_count(*, equals: int | None = None, at_least: int | None = None, at_most: int | None = None) -> RulePredicate:
        def predicate(context: RuleContext) -> bool:
            return _passes(len(u.staff(context.data)), equals=equals, at_least=at_least, at_most=at_most)

        return predicate

    @staticmethod
    def vehicle_count(*, equals: int | None = None, at_least: int | None = None, at_most: int | None = None) -> RulePredicate:
        def predicate(context: RuleContext) -> bool:
            return _passes(len(u.vehicles(context.data)), equals=equals, at_least=at_least, at_most=at_most)

        return predicate

    @staticmethod
    def command_name(name: str | None = None, *, prefix: str | None = None) -> RulePredicate:
        def predicate(context: RuleContext) -> bool:
            logs = u.command_logs(context.data)
            item = getattr(context.event, "item", None)
            if item is not None:
                logs.append(item)
            for entry in logs:
                command = u.get_value(entry, "command")
                command_name = u.command_name(command)
                if name is not None and command_name == u.normalize_text(name):
                    return True
                if prefix is not None and u.normalize_text(command).startswith(u.normalize_text(prefix)):
                    return True
            return False

        return predicate

    @staticmethod
    def emergency_call_age(*, at_least_s: float | None = None, at_most_s: float | None = None) -> RulePredicate:
        def predicate(context: RuleContext) -> bool:
            for call in u.emergency_calls(context.data):
                started_at = u.get_value(call, "started_at")
                if not isinstance(started_at, int):
                    continue
                age = context.now - started_at
                if (at_least_s is None or age >= at_least_s) and (at_most_s is None or age <= at_most_s):
                    return True
            return False

        return predicate

    @staticmethod
    def status_severity(*levels: str) -> RulePredicate:
        wanted = {_SEVERITY_RANK[level] for level in levels if level in _SEVERITY_RANK}

        def predicate(context: RuleContext) -> bool:
            issues = getattr(context.data, "issues", [])
            for issue in issues:
                severity = getattr(issue, "severity", None)
                if severity in _SEVERITY_RANK and _SEVERITY_RANK[severity] in wanted:
                    return True
            return False

        return predicate


__all__ = [
    "AsyncRuleEngine",
    "Conditions",
    "Rule",
    "RuleCallback",
    "RuleContext",
    "RuleEngine",
    "RuleMatch",
    "RulePredicate",
]
