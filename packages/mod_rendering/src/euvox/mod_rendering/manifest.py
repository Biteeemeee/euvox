from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class OperationRecord:
    operation_id: str
    operation_type: str
    schema_version: str
    rendered_files: list[str]
    description: str


@dataclass
class ModManifest:
    mod_version_id: str
    parent_mod_version_id: str | None
    operation_ids: list[str]
    game_version: str
    search_space_version: str
    builder_version: str
    rendered_files: list[str]
    operations: list[OperationRecord] = field(default_factory=list)
    artifact_hash: str = ""
    created_at: str = ""

    def to_dict(self) -> dict[str, object]:
        d = asdict(self)
        d["operations"] = [asdict(op) for op in self.operations]
        return d
