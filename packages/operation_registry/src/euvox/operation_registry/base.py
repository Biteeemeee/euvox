from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class RenderContext:
    mod_version_id: str
    game_version: str
    search_space_version: str


@dataclass
class RenderResult:
    files: dict[str, str]
    description: str


@runtime_checkable
class OperationHandler(Protocol):
    type_name: str
    schema_version: str

    def validate(self, spec: dict[str, object]) -> list[str]:
        """Return a list of validation errors; empty means valid."""
        ...

    def render(self, spec: dict[str, object], context: RenderContext) -> RenderResult:
        ...

    def complexity(self, spec: dict[str, object]) -> float:
        """Relative complexity hint used by the optimizer (0.0 = trivial)."""
        ...

    def describe(self, spec: dict[str, object]) -> str:
        """One-line human-readable summary of what this operation does."""
        ...
