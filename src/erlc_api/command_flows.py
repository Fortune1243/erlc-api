from __future__ import annotations

from dataclasses import dataclass, field
from string import Formatter as StringFormatter
from typing import Any, Iterable, Mapping

from .commands import Command, normalize_command


@dataclass(frozen=True)
class CommandStep:
    command: str | Command
    name: str | None = None
    description: str | None = None
    optional: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def preview(self) -> str:
        return normalize_command(self.command)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "command": self.preview(),
            "description": self.description,
            "optional": self.optional,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CommandTemplate:
    name: str
    template: str
    description: str | None = None

    @property
    def fields(self) -> tuple[str, ...]:
        fields = []
        for _, field_name, _, _ in StringFormatter().parse(self.template):
            if field_name:
                fields.append(field_name)
        return tuple(dict.fromkeys(fields))

    def bind(self, **values: Any) -> CommandStep:
        missing = [field for field in self.fields if field not in values]
        if missing:
            raise KeyError(f"Missing command template value(s): {', '.join(missing)}")
        command = self.template.format(**values)
        return CommandStep(name=self.name, command=command, description=self.description)


@dataclass(frozen=True)
class CommandFlow:
    name: str
    steps: tuple[CommandStep, ...] = field(default_factory=tuple)
    description: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("flow name cannot be blank.")

    def preview(self) -> list[str]:
        return [step.preview() for step in self.steps]

    def validate(self) -> None:
        for step in self.steps:
            step.preview()

    def to_commands(self) -> list[Command]:
        return [Command(step.preview()) for step in self.steps]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "steps": [step.to_dict() for step in self.steps],
        }


class CommandFlowBuilder:
    def __init__(self, name: str, *, description: str | None = None) -> None:
        self.name = name
        self.description = description
        self._steps: list[CommandStep] = []

    def step(
        self,
        command: str | Command,
        *,
        name: str | None = None,
        description: str | None = None,
        optional: bool = False,
        metadata: Mapping[str, Any] | None = None,
    ) -> CommandFlowBuilder:
        self._steps.append(
            CommandStep(
                command=command,
                name=name,
                description=description,
                optional=optional,
                metadata=dict(metadata or {}),
            )
        )
        return self

    def template(self, template: CommandTemplate, **values: Any) -> CommandFlowBuilder:
        self._steps.append(template.bind(**values))
        return self

    def extend(self, flow: CommandFlow | Iterable[CommandStep]) -> CommandFlowBuilder:
        self._steps.extend(flow.steps if isinstance(flow, CommandFlow) else list(flow))
        return self

    def build(self) -> CommandFlow:
        flow = CommandFlow(name=self.name, description=self.description, steps=tuple(self._steps))
        flow.validate()
        return flow


__all__ = [
    "CommandFlow",
    "CommandFlowBuilder",
    "CommandStep",
    "CommandTemplate",
]
