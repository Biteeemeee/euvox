"""Unit tests for operation registry, ModBuilder, and artifact store."""

import hashlib
import json
import zipfile
from io import BytesIO
from pathlib import Path

import pytest
from euvox.mod_rendering import (
    BuildInput,
    ModBuilder,
    OperationInput,
    list_zip_members,
    read_zip_member,
)
from euvox.operation_registry import (
    DEFAULT_REGISTRY,
    NumericPatchV1,
    OperationRegistry,
    RenderContext,
    make_default_registry,
)

# ── NumericPatchV1 validation ─────────────────────────────────────────────────


def test_numeric_patch_valid_spec() -> None:
    handler = NumericPatchV1()
    errors = handler.validate({"target": "war_cost_factor", "value": 1.15, "bounds": [0.5, 2.0]})
    assert errors == []


def test_numeric_patch_missing_fields() -> None:
    handler = NumericPatchV1()
    assert "missing required field: target" in handler.validate({"value": 1.0})
    assert "missing required field: value" in handler.validate({"target": "x"})


def test_numeric_patch_out_of_bounds() -> None:
    handler = NumericPatchV1()
    errors = handler.validate({"target": "x", "value": 3.0, "bounds": [0.5, 2.0]})
    assert any("bounds" in e or "outside" in e for e in errors)


def test_numeric_patch_non_numeric_value() -> None:
    handler = NumericPatchV1()
    errors = handler.validate({"target": "x", "value": "nope"})
    assert any("numeric" in e for e in errors)


# ── NumericPatchV1 rendering ──────────────────────────────────────────────────


def test_numeric_patch_renders_correct_file() -> None:
    handler = NumericPatchV1()
    ctx = RenderContext(
        mod_version_id="mv-test", game_version="1.0.0", search_space_version="v1"
    )
    result = handler.render({"target": "war_cost_factor", "value": 1.15}, ctx)
    assert len(result.files) == 1
    path, content = next(iter(result.files.items()))
    assert path == "common/scripted_values/euvox_war_cost_factor.txt"
    assert "@war_cost_factor = 1.15" in content
    assert "numeric_patch@v1" in content


def test_numeric_patch_complexity_and_describe() -> None:
    handler = NumericPatchV1()
    spec = {"target": "war_cost_factor", "value": 1.15}
    assert handler.complexity(spec) < 1.0
    assert "war_cost_factor" in handler.describe(spec)
    assert "1.15" in handler.describe(spec)


# ── OperationRegistry ─────────────────────────────────────────────────────────


def test_registry_get_registered_handler() -> None:
    registry = make_default_registry()
    handler = registry.get("numeric_patch", "v1")
    assert handler.type_name == "numeric_patch"
    assert handler.schema_version == "v1"


def test_registry_missing_handler_raises() -> None:
    registry = OperationRegistry()
    with pytest.raises(KeyError, match="no_such_op"):
        registry.get("no_such_op", "v1")


def test_default_registry_has_numeric_patch() -> None:
    assert ("numeric_patch", "v1") in DEFAULT_REGISTRY.registered_types()


# ── ModBuilder ────────────────────────────────────────────────────────────────


def _make_build_input(operations: list[OperationInput] | None = None) -> BuildInput:
    return BuildInput(
        mod_version_id="test-mv-001",
        parent_mod_version_id=None,
        operation_ids=["op-1"],
        game_version="1.0.0",
        search_space_version="v1",
        operations=operations
        or [
            OperationInput(
                id="op-1",
                operation_type="numeric_patch",
                schema_version="v1",
                spec={"target": "war_cost_factor", "value": 1.15},
            )
        ],
    )


def test_modbuild_returns_valid_zip() -> None:
    builder = ModBuilder()
    zip_bytes, manifest = builder.build(_make_build_input())
    assert len(zip_bytes) > 0
    with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
        assert zf.testzip() is None


def test_modbuild_zip_contains_expected_files() -> None:
    builder = ModBuilder()
    zip_bytes, _ = builder.build(_make_build_input())
    members = list_zip_members(zip_bytes)
    mod_prefix = [m for m in members if m.endswith("descriptor.mod")]
    assert mod_prefix, "descriptor.mod missing from zip"
    manifest_files = [m for m in members if m.endswith("euvox_manifest.json")]
    assert manifest_files, "euvox_manifest.json missing from zip"
    scripted_values = [m for m in members if "scripted_values" in m]
    assert scripted_values, "scripted_values file missing from zip"


def test_modbuild_manifest_content() -> None:
    builder = ModBuilder()
    zip_bytes, manifest = builder.build(_make_build_input())
    assert manifest.mod_version_id == "test-mv-001"
    assert manifest.game_version == "1.0.0"
    assert manifest.builder_version == "v1"
    assert len(manifest.operations) == 1
    assert manifest.operations[0].operation_type == "numeric_patch"
    assert manifest.artifact_hash.startswith("sha256:")


def test_modbuild_artifact_hash_matches_zip() -> None:
    builder = ModBuilder()
    zip_bytes, manifest = builder.build(_make_build_input())
    expected = "sha256:" + hashlib.sha256(zip_bytes).hexdigest()
    assert manifest.artifact_hash == expected


def test_modbuild_manifest_embedded_in_zip() -> None:
    builder = ModBuilder()
    zip_bytes, manifest = builder.build(_make_build_input())
    members = list_zip_members(zip_bytes)
    manifest_member = next(m for m in members if m.endswith("euvox_manifest.json"))
    raw = read_zip_member(zip_bytes, manifest_member)
    parsed = json.loads(raw)
    assert parsed["mod_version_id"] == "test-mv-001"
    assert len(parsed["operations"]) == 1


def test_modbuild_multiple_operations() -> None:
    ops = [
        OperationInput(
            id=f"op-{i}",
            operation_type="numeric_patch",
            schema_version="v1",
            spec={"target": f"param_{i}", "value": float(i)},
        )
        for i in range(3)
    ]
    build_input = BuildInput(
        mod_version_id="mv-multi",
        parent_mod_version_id=None,
        operation_ids=[o.id for o in ops],
        game_version="1.0.0",
        search_space_version="v1",
        operations=ops,
    )
    builder = ModBuilder()
    zip_bytes, manifest = builder.build(build_input)
    assert len(manifest.operations) == 3
    members = list_zip_members(zip_bytes)
    sv_files = [m for m in members if "scripted_values" in m]
    assert len(sv_files) == 3


def test_modbuild_empty_operations() -> None:
    build_input = BuildInput(
        mod_version_id="mv-empty",
        parent_mod_version_id=None,
        operation_ids=[],
        game_version="1.0.0",
        search_space_version="v1",
    )
    builder = ModBuilder()
    zip_bytes, manifest = builder.build(build_input)
    assert len(manifest.operations) == 0
    members = list_zip_members(zip_bytes)
    assert any(m.endswith("descriptor.mod") for m in members)


# ── LocalArtifactStore ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_local_store_upload_download(tmp_path: Path) -> None:
    from euvox.artifact_store import LocalArtifactStore

    store = LocalArtifactStore(tmp_path)
    data = b"hello artifact"
    uri = await store.upload_bytes("mods", "test.zip", data)
    assert uri.startswith("file://")
    assert await store.exists("mods", "test.zip")
    downloaded = await store.download_bytes("mods", "test.zip")
    assert downloaded == data


@pytest.mark.asyncio
async def test_local_store_not_exists(tmp_path: Path) -> None:
    from euvox.artifact_store import LocalArtifactStore

    store = LocalArtifactStore(tmp_path)
    assert not await store.exists("mods", "missing.zip")
