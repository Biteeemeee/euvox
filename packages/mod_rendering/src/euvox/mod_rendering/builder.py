from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime

from euvox.mod_rendering.manifest import ModManifest, OperationRecord
from euvox.mod_rendering.packager import package_zip
from euvox.operation_registry import DEFAULT_REGISTRY, RenderContext
from euvox.operation_registry.registry import OperationRegistry


@dataclass
class OperationInput:
    id: str
    operation_type: str
    schema_version: str
    spec: dict[str, object]


@dataclass
class BuildInput:
    mod_version_id: str
    parent_mod_version_id: str | None
    operation_ids: list[str]
    game_version: str
    search_space_version: str
    operations: list[OperationInput] = field(default_factory=list)


BUILDER_VERSION = "v1"


class ModBuilder:
    def __init__(self, registry: OperationRegistry | None = None) -> None:
        self._registry = registry or DEFAULT_REGISTRY

    def build(self, input: BuildInput) -> tuple[bytes, ModManifest]:
        context = RenderContext(
            mod_version_id=input.mod_version_id,
            game_version=input.game_version,
            search_space_version=input.search_space_version,
        )

        all_files: dict[str, str] = {}
        op_records: list[OperationRecord] = []

        for op in input.operations:
            handler = self._registry.get(op.operation_type, op.schema_version)
            result = handler.render(op.spec, context)
            all_files.update(result.files)
            op_records.append(
                OperationRecord(
                    operation_id=op.id,
                    operation_type=op.operation_type,
                    schema_version=op.schema_version,
                    rendered_files=list(result.files),
                    description=result.description,
                )
            )

        mod_name = f"euvox_{input.mod_version_id[:8]}"
        all_files["descriptor.mod"] = self._render_descriptor(mod_name, input.game_version)

        manifest = ModManifest(
            mod_version_id=input.mod_version_id,
            parent_mod_version_id=input.parent_mod_version_id,
            operation_ids=input.operation_ids,
            game_version=input.game_version,
            search_space_version=input.search_space_version,
            builder_version=BUILDER_VERSION,
            rendered_files=sorted(all_files),
            operations=op_records,
            created_at=datetime.now(UTC).isoformat(),
        )

        all_files["euvox_manifest.json"] = _json_dumps(manifest.to_dict())
        zip_bytes = package_zip(all_files, mod_name)
        manifest.artifact_hash = f"sha256:{hashlib.sha256(zip_bytes).hexdigest()}"

        return zip_bytes, manifest

    @staticmethod
    def _render_descriptor(mod_name: str, game_version: str) -> str:
        return (
            f'name="{mod_name}"\n'
            f'version="0.1"\n'
            f'supported_version="{game_version}"\n'
            f'tags={{\n'
            f'    "Generated"\n'
            f"}}\n"
        )


def _json_dumps(obj: object) -> str:
    import json

    return json.dumps(obj, indent=2, default=str)
