from euvox.agent_protocol import AgentReview, AgentVerdict, EventProposal

_REGION_DEFAULT_EFFECTS: dict[str, str] = {
    "anatolia": "add_prestige = 10",
    "western_europe": "add_stability = 1",
    "eastern_europe": "add_manpower = 500",
    "iberia": "add_treasury = 50",
    "middle_east": "add_piety = 10",
    "north_africa": "add_administrative_power = 10",
}
_FALLBACK_EFFECT = "add_prestige = 5"


class TemplateDesignerAgent:
    name = "template_designer_agent"
    version = "v1"

    def review(self, proposal: EventProposal) -> AgentReview:
        modified = proposal.model_copy(deep=True)
        changes: list[str] = []

        if not modified.description:
            modified.description = (
                f"Historical event: {modified.title}"
                + (f" ({modified.era})" if modified.era else "")
                + "."
            )
            changes.append("Generated template description.")

        if not modified.effects:
            default = _REGION_DEFAULT_EFFECTS.get(modified.region.lower(), _FALLBACK_EFFECT)
            modified.effects = [default]
            changes.append(f"Added default effect for region '{modified.region or 'unknown'}'.")

        if not modified.era and modified.trigger_conditions:
            for cond in modified.trigger_conditions:
                if "year >=" in cond:
                    try:
                        year = int(cond.split("year >=")[1].strip())
                        modified.era = f"{year}-{year + 50}"
                        changes.append(f"Inferred era from trigger condition: {modified.era}.")
                        break
                    except ValueError:
                        pass

        if changes:
            return AgentReview(
                agent_name=self.name,
                agent_version=self.version,
                verdict=AgentVerdict.MODIFIED,
                confidence=0.7,
                reasoning="Filled in missing template fields.",
                suggestions=changes,
                modified_proposal=modified,
            )

        return AgentReview(
            agent_name=self.name,
            agent_version=self.version,
            verdict=AgentVerdict.ACCEPTED,
            confidence=0.9,
            reasoning="Proposal is already complete; no modifications needed.",
        )
