import re

from euvox.agent_protocol import AgentReview, AgentVerdict, EventProposal

_EFFECT_VAR_RE = re.compile(r"(add|remove|set|subtract)_(\w+)")


def _extract_variable(effect: str) -> str | None:
    m = _EFFECT_VAR_RE.search(effect)
    return m.group(2) if m else None


class RuleBasedCounterfactualAgent:
    name = "counterfactual_agent"
    version = "v1"

    def review(self, proposal: EventProposal) -> AgentReview:
        failures: list[str] = []
        suggestions: list[str] = []

        if proposal.is_major and not proposal.trigger_conditions:
            failures.append("Major events must have at least one trigger condition.")

        # Detect contradictory effects on the same variable
        add_vars: set[str] = set()
        remove_vars: set[str] = set()
        for effect in proposal.effects:
            var = _extract_variable(effect)
            if var is None:
                continue
            if effect.lstrip().startswith(("add_", "set_")):
                add_vars.add(var)
            elif effect.lstrip().startswith(("remove_", "subtract_")):
                remove_vars.add(var)

        conflicts = add_vars & remove_vars
        for var in sorted(conflicts):
            failures.append(f"Contradictory effects on variable '{var}'.")

        if not proposal.effects:
            suggestions.append("An event with no effects has no gameplay impact.")

        if failures:
            return AgentReview(
                agent_name=self.name,
                agent_version=self.version,
                verdict=AgentVerdict.REJECTED,
                confidence=0.95,
                reasoning="; ".join(failures),
                suggestions=suggestions,
            )

        return AgentReview(
            agent_name=self.name,
            agent_version=self.version,
            verdict=AgentVerdict.ACCEPTED,
            confidence=0.8,
            reasoning="Counterfactual consistency checks passed.",
            suggestions=suggestions,
        )
