from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any

from . import _utility as u
from .models import Model


class SchemaInspector:
    """Inspect typed models and raw/extra payload preservation."""

    def __init__(self, value: Any) -> None:
        self.value = value

    def fields(self) -> list[str]:
        target = self.value
        if isinstance(target, list) and target:
            target = target[0]
        if is_dataclass(target):
            return [field.name for field in fields(target)]
        if isinstance(target, dict):
            return list(target.keys())
        return []

    def raw(self) -> Any:
        if isinstance(self.value, Model):
            return self.value.raw
        return u.model_dict(self.value)

    def extra(self) -> dict[str, Any]:
        if isinstance(self.value, Model):
            return dict(self.value.extra)
        return {}

    def missing(self, *names: str) -> list[str]:
        available = set(self.fields())
        return [name for name in names if name not in available]

    def diagnostics(self, *required: str) -> dict[str, Any]:
        return {
            "type": type(self.value).__name__,
            "fields": self.fields(),
            "missing": self.missing(*required),
            "extra_keys": list(self.extra().keys()),
            "has_raw": bool(self.raw()),
        }


__all__ = ["SchemaInspector"]
