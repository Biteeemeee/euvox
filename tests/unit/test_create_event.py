"""Unit tests for the create_event@v1 operation: validation, rendering, golden files."""

from pathlib import Path

import pytest
from euvox.agent_protocol import EventProposal
from euvox.operation_registry import CreateEventV1, RenderContext

GOLDEN_DIR = Path(__file__).parent.parent / "golden" / "create_event"


def _ctx() -> RenderContext:
    return RenderContext(
        mod_version_id="mv-test",
        game_version="1.0.0",
        search_space_version="v1",
    )


def _ottoman_spec() -> dict:
    return {
        "event_id": "euvox.ottoman.001",
        "title": "Ottoman Expansion",
        "description": "The Ottomans consolidate their position in Anatolia.",
        "trigger_conditions": ["tag = TUR", "year >= 1444"],
        "effects": [],
        "options": [
            {
                "name": "euvox.ottoman.001.a",
                "tooltip": "Embrace our destiny.",
                "effects": ["add_prestige = 10", "add_manpower = 500"],
            }
        ],
        "picture": "GFX_evt_default",
        "is_triggered_only": True,
        "fire_only_once": True,
    }


def _byzantine_spec() -> dict:
    return {
        "event_id": "euvox.byzantine.revival",
        "title": "The Byzantine Revival",
        "description": "Historical event: The Byzantine Revival (1444-1490).",
        "trigger_conditions": ["tag = BYZ", "year >= 1444"],
        "effects": ["add_manpower = 500"],
        "options": [],
        "picture": "GFX_evt_default",
        "is_triggered_only": True,
        "fire_only_once": True,
    }


# ── Validation ────────────────────────────────────────────────────────────────


def test_validate_accepts_valid_spec() -> None:
    handler = CreateEventV1()
    errors = handler.validate(_ottoman_spec())
    assert errors == []


def test_validate_rejects_missing_event_id() -> None:
    handler = CreateEventV1()
    spec = _ottoman_spec()
    del spec["event_id"]
    errors = handler.validate(spec)
    assert any("event_id" in e for e in errors)


def test_validate_rejects_missing_title() -> None:
    handler = CreateEventV1()
    spec = {**_ottoman_spec(), "title": ""}
    errors = handler.validate(spec)
    assert any("title" in e for e in errors)


def test_validate_rejects_option_without_name() -> None:
    handler = CreateEventV1()
    spec = {**_ottoman_spec(), "options": [{"effects": ["add_prestige = 5"]}]}
    errors = handler.validate(spec)
    assert any("option[0]" in e for e in errors)


def test_validate_rejects_non_list_trigger_conditions() -> None:
    handler = CreateEventV1()
    spec = {**_ottoman_spec(), "trigger_conditions": "tag = TUR"}
    errors = handler.validate(spec)
    assert any("trigger_conditions" in e for e in errors)


# ── Render — file paths ───────────────────────────────────────────────────────


def test_render_produces_two_files() -> None:
    handler = CreateEventV1()
    result = handler.render(_ottoman_spec(), _ctx())
    assert len(result.files) == 2


def test_render_file_paths_correct() -> None:
    handler = CreateEventV1()
    result = handler.render(_ottoman_spec(), _ctx())
    assert "events/euvox_euvox_ottoman_001.txt" in result.files
    assert "localisation/english/euvox_euvox_ottoman_001_l_english.yml" in result.files


def test_render_description_contains_event_id() -> None:
    handler = CreateEventV1()
    result = handler.render(_ottoman_spec(), _ctx())
    assert "euvox.ottoman.001" in result.description


# ── Golden-file tests ─────────────────────────────────────────────────────────


def test_render_ottoman_event_script_matches_golden() -> None:
    handler = CreateEventV1()
    result = handler.render(_ottoman_spec(), _ctx())
    script = result.files["events/euvox_euvox_ottoman_001.txt"]
    expected = (GOLDEN_DIR / "ottoman_expansion.txt").read_text()
    assert script == expected


def test_render_ottoman_localization_matches_golden() -> None:
    handler = CreateEventV1()
    result = handler.render(_ottoman_spec(), _ctx())
    loc = result.files["localisation/english/euvox_euvox_ottoman_001_l_english.yml"]
    expected = (GOLDEN_DIR / "ottoman_expansion_l_english.yml").read_text()
    assert loc == expected


def test_render_byzantine_auto_option_matches_golden() -> None:
    handler = CreateEventV1()
    result = handler.render(_byzantine_spec(), _ctx())
    script = result.files["events/euvox_euvox_byzantine_revival.txt"]
    expected = (GOLDEN_DIR / "byzantine_revival.txt").read_text()
    assert script == expected


def test_render_byzantine_localization_auto_option_matches_golden() -> None:
    handler = CreateEventV1()
    result = handler.render(_byzantine_spec(), _ctx())
    loc = result.files["localisation/english/euvox_euvox_byzantine_revival_l_english.yml"]
    expected = (GOLDEN_DIR / "byzantine_revival_l_english.yml").read_text()
    assert loc == expected


# ── Complexity and describe ───────────────────────────────────────────────────


def test_complexity_no_options() -> None:
    handler = CreateEventV1()
    assert handler.complexity(_byzantine_spec()) == pytest.approx(1.0)


def test_complexity_one_option() -> None:
    handler = CreateEventV1()
    assert handler.complexity(_ottoman_spec()) == pytest.approx(1.2)


def test_describe_includes_event_id_and_title() -> None:
    handler = CreateEventV1()
    desc = handler.describe(_ottoman_spec())
    assert "euvox.ottoman.001" in desc
    assert "Ottoman Expansion" in desc


# ── Registry integration ──────────────────────────────────────────────────────


def test_create_event_registered_in_default_registry() -> None:
    from euvox.operation_registry import DEFAULT_REGISTRY

    handler = DEFAULT_REGISTRY.get("create_event", "v1")
    assert handler is not None
    assert handler.type_name == "create_event"


# ── EventProposal.to_create_event_spec ───────────────────────────────────────


def test_proposal_to_spec_roundtrip() -> None:
    proposal = EventProposal(
        event_id="euvox.test.spec",
        title="Test Spec Event",
        description="A test.",
        era="1444-1500",
        region="anatolia",
        trigger_conditions=["tag = TUR"],
        effects=["add_prestige = 5"],
    )
    spec = proposal.to_create_event_spec()
    assert spec["event_id"] == proposal.event_id
    assert spec["title"] == proposal.title
    assert spec["trigger_conditions"] == proposal.trigger_conditions
    assert spec["effects"] == proposal.effects
    assert spec["options"] == []
    assert spec["is_triggered_only"] is True

    # spec must be valid
    handler = CreateEventV1()
    errors = handler.validate(spec)
    assert errors == []


def test_proposal_to_spec_renders_without_error() -> None:
    proposal = EventProposal(
        event_id="euvox.test.render",
        title="Render Test",
        description="Renders fine.",
        trigger_conditions=["year >= 1500"],
        effects=["add_stability = 1"],
    )
    spec = proposal.to_create_event_spec()
    handler = CreateEventV1()
    result = handler.render(spec, _ctx())
    assert "events/" in list(result.files.keys())[0]
    assert "year >= 1500" in list(result.files.values())[0]
