"""Unit tests for the three rule-based agents."""


from agent_service.agents.counterfactual import RuleBasedCounterfactualAgent
from agent_service.agents.designer import TemplateDesignerAgent
from agent_service.agents.history import RuleBasedHistoryAgent
from euvox.agent_protocol import AgentVerdict, EventProposal


def _proposal(**kwargs) -> EventProposal:
    defaults = dict(
        event_id="eu5.test.001",
        title="The Test Event",
        era="1444-1500",
        region="anatolia",
        trigger_conditions=["tag = TUR"],
        effects=["add_prestige = 10"],
        is_major=False,
    )
    defaults.update(kwargs)
    return EventProposal(**defaults)


# ── RuleBasedHistoryAgent ─────────────────────────────────────────────────────


def test_history_accepts_valid_proposal() -> None:
    agent = RuleBasedHistoryAgent()
    review = agent.review(_proposal())
    assert review.verdict == AgentVerdict.ACCEPTED


def test_history_rejects_empty_title() -> None:
    agent = RuleBasedHistoryAgent()
    review = agent.review(_proposal(title=""))
    assert review.verdict == AgentVerdict.REJECTED
    assert "title" in review.reasoning.lower()


def test_history_rejects_out_of_range_era() -> None:
    agent = RuleBasedHistoryAgent()
    review = agent.review(_proposal(era="1900-1950"))
    assert review.verdict == AgentVerdict.REJECTED
    assert "timeline" in review.reasoning.lower()


def test_history_rejects_bad_era_format() -> None:
    agent = RuleBasedHistoryAgent()
    review = agent.review(_proposal(era="early_modern"))
    assert review.verdict == AgentVerdict.REJECTED


def test_history_rejects_anachronistic_term() -> None:
    agent = RuleBasedHistoryAgent()
    review = agent.review(_proposal(title="The Nuclear Age Begins"))
    assert review.verdict == AgentVerdict.REJECTED
    assert "nuclear" in review.reasoning.lower()


def test_history_suggests_era_when_missing() -> None:
    agent = RuleBasedHistoryAgent()
    review = agent.review(_proposal(era=""))
    assert review.verdict == AgentVerdict.ACCEPTED
    assert any("era" in s.lower() for s in review.suggestions)


def test_history_rejects_reversed_era() -> None:
    agent = RuleBasedHistoryAgent()
    review = agent.review(_proposal(era="1600-1500"))
    assert review.verdict == AgentVerdict.REJECTED


# ── RuleBasedCounterfactualAgent ──────────────────────────────────────────────


def test_counterfactual_accepts_valid_proposal() -> None:
    agent = RuleBasedCounterfactualAgent()
    review = agent.review(_proposal())
    assert review.verdict == AgentVerdict.ACCEPTED


def test_counterfactual_rejects_major_with_no_triggers() -> None:
    agent = RuleBasedCounterfactualAgent()
    review = agent.review(_proposal(is_major=True, trigger_conditions=[]))
    assert review.verdict == AgentVerdict.REJECTED
    assert "major" in review.reasoning.lower()


def test_counterfactual_rejects_contradictory_effects() -> None:
    agent = RuleBasedCounterfactualAgent()
    review = agent.review(
        _proposal(effects=["add_stability = 1", "remove_stability = 1"])
    )
    assert review.verdict == AgentVerdict.REJECTED
    assert "stability" in review.reasoning.lower()


def test_counterfactual_warns_empty_effects() -> None:
    agent = RuleBasedCounterfactualAgent()
    review = agent.review(_proposal(effects=[]))
    assert review.verdict == AgentVerdict.ACCEPTED
    assert any("no effects" in s.lower() for s in review.suggestions)


# ── TemplateDesignerAgent ─────────────────────────────────────────────────────


def test_designer_accepts_complete_proposal() -> None:
    agent = TemplateDesignerAgent()
    review = agent.review(_proposal(description="A fully specified event."))
    assert review.verdict == AgentVerdict.ACCEPTED
    assert review.modified_proposal is None


def test_designer_fills_missing_description() -> None:
    agent = TemplateDesignerAgent()
    review = agent.review(_proposal(description=""))
    assert review.verdict == AgentVerdict.MODIFIED
    assert review.modified_proposal is not None
    assert review.modified_proposal.description != ""


def test_designer_adds_default_effect_for_known_region() -> None:
    agent = TemplateDesignerAgent()
    review = agent.review(_proposal(effects=[], region="anatolia"))
    assert review.verdict == AgentVerdict.MODIFIED
    assert review.modified_proposal is not None
    assert len(review.modified_proposal.effects) == 1
    assert "prestige" in review.modified_proposal.effects[0]


def test_designer_infers_era_from_trigger() -> None:
    agent = TemplateDesignerAgent()
    review = agent.review(
        _proposal(era="", trigger_conditions=["year >= 1500"])
    )
    assert review.verdict == AgentVerdict.MODIFIED
    assert review.modified_proposal is not None
    assert review.modified_proposal.era == "1500-1550"


def test_designer_uses_fallback_effect_for_unknown_region() -> None:
    agent = TemplateDesignerAgent()
    review = agent.review(_proposal(effects=[], region="unknown_place"))
    assert review.verdict == AgentVerdict.MODIFIED
    assert review.modified_proposal is not None
    assert review.modified_proposal.effects  # non-empty
