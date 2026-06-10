"""Integration test: agent review → create_event spec → mod file rendering."""

from pathlib import Path

import httpx
import pytest
from agent_service.config import Settings as AgentSettings
from agent_service.tasks import review_event_proposal
from control_api.main import app
from euvox.agent_protocol import AgentVerdict, EventProposal
from euvox.core.models import Base
from euvox.core.repositories import AgentReviewRepository
from euvox.operation_registry import DEFAULT_REGISTRY, CreateEventV1, RenderContext
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.fixture
async def pipeline_db(tmp_path: Path):
    db_file = tmp_path / "pipeline_test.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"
    engine = create_async_engine(db_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    app.state.engine = engine
    app.state.session_factory = factory

    yield engine, factory, db_url

    del app.state.engine
    del app.state.session_factory
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def test_full_pipeline_review_then_render(pipeline_db, tmp_path: Path) -> None:
    """Proposal passes agents → converted to spec → rendered to mod files."""
    engine, factory, db_url = pipeline_db

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        r = await http.post(
            "/experiments",
            json={
                "name": "Pipeline Test",
                "target_set_version": "v1",
                "search_space_version": "v1",
            },
        )
        experiment_id = r.json()["id"]

    proposal = EventProposal(
        event_id="euvox.pipeline.001",
        title="The Pipeline Test",
        description="An event created to test the full pipeline.",
        era="1444-1600",
        region="western_europe",
        trigger_conditions=["tag = FRA", "year >= 1500"],
        effects=["add_stability = 1"],
        is_major=False,
    )

    settings = AgentSettings(database_url=db_url)
    final_proposal, reviews = await review_event_proposal(proposal, experiment_id, settings)

    assert all(r.verdict != AgentVerdict.REJECTED for r in reviews)

    # Convert to create_event spec
    spec = final_proposal.to_create_event_spec()
    errors = CreateEventV1().validate(spec)
    assert errors == [], f"Spec validation failed: {errors}"

    # Render via registry
    ctx = RenderContext(
        mod_version_id="mv-pipeline-001",
        game_version="1.0.0",
        search_space_version="v1",
    )
    result = DEFAULT_REGISTRY.get("create_event", "v1").render(spec, ctx)

    assert len(result.files) == 2
    script_key = [k for k in result.files if k.endswith(".txt")][0]
    loc_key = [k for k in result.files if k.endswith(".yml")][0]

    script = result.files[script_key]
    assert "euvox.pipeline.001" in script
    assert '# The Pipeline Test' in script  # title appears as a comment line
    assert 'title = "euvox.pipeline.001.t"' in script  # loc key used for in-game title
    assert "tag = FRA" in script
    assert "year >= 1500" in script
    assert "add_stability = 1" in script

    loc = result.files[loc_key]
    assert '"The Pipeline Test"' in loc
    assert '"An event created to test the full pipeline."' in loc

    # Reviews persisted in DB
    async with factory() as session:
        records = await AgentReviewRepository(session).list_by_experiment(experiment_id)
    assert len(records) == 3


async def test_rejected_proposal_does_not_render(pipeline_db, tmp_path: Path) -> None:
    """A proposal rejected by agents should not be rendered."""
    _, _, db_url = pipeline_db

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        r = await http.post(
            "/experiments",
            json={"name": "Reject Test", "target_set_version": "v1", "search_space_version": "v1"},
        )
        experiment_id = r.json()["id"]

    bad_proposal = EventProposal(
        event_id="euvox.bad.001",
        title="",  # empty → history agent rejects
        era="1444-1500",
        trigger_conditions=["tag = FRA"],
        effects=["add_prestige = 5"],
    )

    settings = AgentSettings(database_url=db_url)
    _, reviews = await review_event_proposal(bad_proposal, experiment_id, settings)

    assert any(r.verdict == AgentVerdict.REJECTED for r in reviews)

    # Validate spec would fail too
    spec = bad_proposal.to_create_event_spec()
    errors = CreateEventV1().validate(spec)
    assert any("title" in e for e in errors)
