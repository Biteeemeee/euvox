"""Integration test: event proposals run through the full agent pipeline and persist reviews."""

from pathlib import Path

import httpx
import pytest
from agent_service.config import Settings as AgentSettings
from agent_service.tasks import review_event_proposal
from control_api.main import app
from euvox.agent_protocol import AgentVerdict, EventProposal
from euvox.core.models import Base
from euvox.core.repositories import AgentReviewRepository
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.fixture
async def agent_db(tmp_path: Path):
    db_file = tmp_path / "agent_test.db"
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


async def test_valid_proposal_accepted_and_persisted(agent_db, tmp_path: Path) -> None:
    """A valid complete proposal passes all agents and is persisted as 3 review records."""
    engine, factory, db_url = agent_db

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        r = await http.post(
            "/experiments",
            json={
                "name": "Agent Test",
                "target_set_version": "v1",
                "search_space_version": "v1",
            },
        )
        experiment_id = r.json()["id"]

    proposal = EventProposal(
        event_id="eu5.test.valid_001",
        title="Ottoman Expansion",
        description="The Ottomans consolidate their position in Anatolia.",
        era="1444-1500",
        region="anatolia",
        trigger_conditions=["tag = TUR", "year >= 1444"],
        effects=["add_prestige = 10", "add_manpower = 500"],
        is_major=False,
    )

    settings = AgentSettings(database_url=db_url)
    final_proposal, reviews = await review_event_proposal(proposal, experiment_id, settings)

    assert final_proposal.event_id == proposal.event_id
    assert len(reviews) == 3
    assert all(r.verdict != AgentVerdict.REJECTED for r in reviews)

    async with factory() as session:
        repo = AgentReviewRepository(session)
        records = await repo.list_by_experiment(experiment_id)

    assert len(records) == 3
    agent_names = {r.agent_name for r in records}
    assert "history_agent" in agent_names
    assert "counterfactual_agent" in agent_names
    assert "template_designer_agent" in agent_names


async def test_rejected_proposal_stops_pipeline(agent_db, tmp_path: Path) -> None:
    """A rejected proposal stops after the first rejecting agent."""
    engine, factory, db_url = agent_db

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        r = await http.post(
            "/experiments",
            json={"name": "Reject Test", "target_set_version": "v1", "search_space_version": "v1"},
        )
        experiment_id = r.json()["id"]

    # Empty title → rejected by history_agent (first agent)
    proposal = EventProposal(
        event_id="eu5.test.bad_001",
        title="",
        era="1444-1500",
        region="anatolia",
        trigger_conditions=["tag = TUR"],
        effects=["add_prestige = 5"],
    )

    settings = AgentSettings(database_url=db_url)
    _, reviews = await review_event_proposal(proposal, experiment_id, settings)

    assert reviews[0].verdict == AgentVerdict.REJECTED
    # Pipeline stops: only 1 review persisted
    async with factory() as session:
        records = await AgentReviewRepository(session).list_by_experiment(experiment_id)
    assert len(records) == 1
    assert records[0].verdict == AgentVerdict.REJECTED


async def test_incomplete_proposal_enriched_by_designer(agent_db, tmp_path: Path) -> None:
    """A proposal missing description and effects is enriched by the designer agent."""
    engine, factory, db_url = agent_db

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        r = await http.post(
            "/experiments",
            json={
                "name": "Designer Test",
                "target_set_version": "v1",
                "search_space_version": "v1",
            },
        )
        experiment_id = r.json()["id"]

    proposal = EventProposal(
        event_id="eu5.test.incomplete_001",
        title="The Byzantine Revival",
        era="1444-1490",
        region="eastern_europe",
        trigger_conditions=["tag = BYZ"],
        effects=[],
        description="",
    )

    settings = AgentSettings(database_url=db_url)
    final_proposal, reviews = await review_event_proposal(proposal, experiment_id, settings)

    designer_review = next(r for r in reviews if r.agent_name == "template_designer_agent")
    assert designer_review.verdict == AgentVerdict.MODIFIED
    assert final_proposal.description != ""
    assert len(final_proposal.effects) > 0
