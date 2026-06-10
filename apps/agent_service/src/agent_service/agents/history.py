import re

from euvox.agent_protocol import AgentReview, AgentVerdict, EventProposal

_GAME_START_YEAR = 1444
_GAME_END_YEAR = 1821

_ANACHRONISTIC_TERMS = frozenset(
    ["nuclear", "tank", "airplane", "rocket", "computer", "internet", "telegram"]
)

_ERA_RE = re.compile(r"^(\d{4})-(\d{4})$")


class RuleBasedHistoryAgent:
    name = "history_agent"
    version = "v1"

    def review(self, proposal: EventProposal) -> AgentReview:
        failures: list[str] = []
        suggestions: list[str] = []

        if not proposal.title.strip():
            failures.append("Event title must not be empty.")

        if proposal.era:
            m = _ERA_RE.match(proposal.era)
            if not m:
                failures.append(f"Era '{proposal.era}' must be in YYYY-YYYY format.")
            else:
                start, end = int(m.group(1)), int(m.group(2))
                if start > end:
                    failures.append("Era start year must not exceed end year.")
                if start < _GAME_START_YEAR or end > _GAME_END_YEAR:
                    failures.append(
                        f"Era must fall within game timeline "
                        f"{_GAME_START_YEAR}-{_GAME_END_YEAR}."
                    )

        text = (proposal.title + " " + proposal.description).lower()
        for term in _ANACHRONISTIC_TERMS:
            if term in text:
                failures.append(f"Anachronistic term detected: '{term}'.")

        if failures:
            return AgentReview(
                agent_name=self.name,
                agent_version=self.version,
                verdict=AgentVerdict.REJECTED,
                confidence=0.9,
                reasoning="; ".join(failures),
                suggestions=suggestions,
            )

        if not proposal.era:
            suggestions.append("Consider specifying an era for better historical grounding.")

        return AgentReview(
            agent_name=self.name,
            agent_version=self.version,
            verdict=AgentVerdict.ACCEPTED,
            confidence=0.85,
            reasoning="Historical plausibility checks passed.",
            suggestions=suggestions,
        )
