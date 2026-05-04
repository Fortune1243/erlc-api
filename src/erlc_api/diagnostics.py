from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from ._errors import APIError, RateLimitError
from .commands import infer_command_success
from .error_codes import explain_error_code


_RANK = {"ok": 0, "info": 1, "warning": 2, "error": 3, "critical": 4}


@dataclass(frozen=True)
class Diagnostic:
    severity: str
    message: str
    advice: str | None = None
    code: str | int | None = None
    source: str | None = None
    retryable: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "message": self.message,
            "advice": self.advice,
            "code": self.code,
            "source": self.source,
            "retryable": self.retryable,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class Diagnostics:
    items: list[Diagnostic] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(_RANK.get(item.severity, 0) >= _RANK["warning"] for item in self.items)

    @property
    def highest_severity(self) -> str:
        if not self.items:
            return "ok"
        return max((item.severity for item in self.items), key=lambda item: _RANK.get(item, 0))

    def extend(self, items: Iterable[Diagnostic]) -> Diagnostics:
        return Diagnostics([*self.items, *list(items)])

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "highest_severity": self.highest_severity,
            "items": [item.to_dict() for item in self.items],
        }


def diagnose_error(error: Exception) -> Diagnostics:
    if isinstance(error, RateLimitError):
        retry_after = getattr(error, "retry_after", None)
        advice = f"Wait {retry_after:g}s before retrying." if retry_after is not None else "Wait for the rate-limit reset before retrying."
        return Diagnostics(
            [
                Diagnostic(
                    severity="warning",
                    message=str(error),
                    advice=advice,
                    code=error.error_code,
                    source="rate_limit",
                    retryable=True,
                    metadata={"bucket": error.bucket, "retry_after": retry_after, "reset_epoch_s": error.reset_epoch_s},
                )
            ]
        )

    if isinstance(error, APIError):
        info = explain_error_code(error.error_code) if error.error_code is not None else None
        return Diagnostics(
            [
                Diagnostic(
                    severity="warning" if info and info.retryable else "error",
                    message=info.message if info is not None else str(error),
                    advice=info.advice if info is not None else None,
                    code=error.error_code,
                    source="api_error",
                    retryable=bool(info and info.retryable),
                    metadata={"status": error.status, "method": error.method, "path": error.path},
                )
            ]
        )

    return Diagnostics([Diagnostic(severity="error", message=str(error), source=type(error).__name__)])


def diagnose_rate_limits(snapshot: Any) -> Diagnostics:
    states = getattr(snapshot, "states", snapshot)
    if isinstance(states, Mapping):
        iterable = states.values()
    else:
        iterable = states or []
    diagnostics: list[Diagnostic] = []
    for state in iterable:
        remaining = getattr(state, "remaining", None)
        retry_after = getattr(state, "retry_after_s", None)
        reset = getattr(state, "reset_epoch_s", None)
        bucket = getattr(state, "bucket", None)
        if remaining == 0 or retry_after is not None:
            diagnostics.append(
                Diagnostic(
                    severity="warning",
                    message=f"Rate-limit bucket {bucket or 'unknown'} is exhausted or cooling down.",
                    advice="Reduce polling frequency or wait for the reset.",
                    code="rate_limit_bucket",
                    source="rate_limit",
                    retryable=True,
                    metadata={"bucket": bucket, "remaining": remaining, "retry_after": retry_after, "reset_epoch_s": reset},
                )
            )
    return Diagnostics(diagnostics)


def diagnose_validation(result: Any) -> Diagnostics:
    status = str(getattr(result, "status", result))
    if status.endswith("OK") or status == "ok" or status.endswith(".OK"):
        return Diagnostics([])
    return Diagnostics(
        [
            Diagnostic(
                severity="warning" if "rate" in status.lower() else "error",
                message=f"Validation status is {status}.",
                advice="Check credentials, network access, or rate-limit state.",
                code=status,
                source="validation",
            )
        ]
    )


def diagnose_command_result(result: Any) -> Diagnostics:
    success = infer_command_success(success=getattr(result, "success", None), message=getattr(result, "message", None))
    if success is True:
        return Diagnostics([])
    severity = "warning" if success is None else "error"
    return Diagnostics(
        [
            Diagnostic(
                severity=severity,
                message=getattr(result, "message", None) or "Command result did not confirm success.",
                advice="Inspect the command text and PRC response message.",
                source="command",
            )
        ]
    )


def diagnose_status(status: Any) -> Diagnostics:
    diagnostics = []
    for issue in getattr(status, "issues", []) or []:
        diagnostics.append(
            Diagnostic(
                severity=getattr(issue, "severity", "info"),
                message=getattr(issue, "message", str(issue)),
                advice=getattr(issue, "advice", None),
                code=getattr(issue, "code", None),
                source="status",
            )
        )
    return Diagnostics(diagnostics)


__all__ = [
    "Diagnostic",
    "Diagnostics",
    "diagnose_command_result",
    "diagnose_error",
    "diagnose_rate_limits",
    "diagnose_status",
    "diagnose_validation",
]
