import structlog
from euvox.agent_protocol import AgentReview, AgentVerdict, EventProposal
from euvox.core.db import make_engine, make_session_factory
from euvox.core.models.agent_review import AgentReviewRecord
from euvox.core.repositories import AgentReviewRepository

from agent_service.agents.counterfactual import RuleBasedCounterfactualAgent
from agent_service.agents.designer import TemplateDesignerAgent
from agent_service.agents.history import RuleBasedHistoryAgent
from agent_service.config import Settings, get_settings

logger = structlog.get_logger()

_AGENTS = [
    RuleBasedHistoryAgent(),
    RuleBasedCounterfactualAgent(),
    TemplateDesignerAgent(),
]


async def review_event_proposal(
    proposal: EventProposal,
    experiment_id: str,
    settings: Settings | None = None,
) -> tuple[EventProposal, list[AgentReview]]:
    """Run all agents on the proposal.

    Returns the final (possibly modified) proposal and the list of all reviews.
    Hard-rejects if any agent returns REJECTED.
    """
    if settings is None:
        settings = get_settings()

    log = logger.bind(experiment_id=experiment_id, event_id=proposal.event_id)
    log.info("agent_review_started", agents=[a.name for a in _AGENTS])

    current_proposal = proposal
    reviews: list[AgentReview] = []

    engine = make_engine(settings.database_url)
    factory = make_session_factory(engine)

    try:
        for agent in _AGENTS:
            review = agent.review(current_proposal)
            reviews.append(review)

            async with factory() as session, session.begin():
                repo = AgentReviewRepository(session)
                record = AgentReviewRecord(
                    experiment_id=experiment_id,
                    proposal_hash=current_proposal.canonical_hash(),
                    agent_name=review.agent_name,
                    agent_version=review.agent_version,
                    verdict=review.verdict,
                    confidence=review.confidence,
                    reasoning=review.reasoning,
                    suggestions=review.suggestions,
                    modified_proposal=(
                        review.modified_proposal.model_dump()
                        if review.modified_proposal
                        else None
                    ),
                )
                await repo.create(record)

            log.info(
                "agent_reviewed",
                agent=review.agent_name,
                verdict=review.verdict,
                confidence=review.confidence,
            )

            if review.verdict == AgentVerdict.REJECTED:
                log.info("proposal_rejected", agent=review.agent_name)
                return current_proposal, reviews

            if review.verdict == AgentVerdict.MODIFIED and review.modified_proposal:
                current_proposal = review.modified_proposal

        log.info("proposal_accepted", final_proposal_id=current_proposal.event_id)
        return current_proposal, reviews

    finally:
        await engine.dispose()
