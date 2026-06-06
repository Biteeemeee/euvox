# Agent Layer

## Purpose

Agents help validate, enrich, and describe structural operations such as new events or situations. Agents must not directly write unvalidated mod code.

## Agent Roles

### HistoryAgent

Checks historical plausibility.

Input:

```json
{
  "operation_type": "create_event",
  "theme": "Louisiana transfer to Spain",
  "primary_tag": "FRA",
  "secondary_tag": "SPA",
  "epoch": [1756, 1770],
  "effect": "transfer_louisiana_from_france_to_spain"
}
```

Output:

```json
{
  "verdict": "accept_with_constraints",
  "plausibility_score": 0.93,
  "required_conditions": [
    "France controls Louisiana",
    "France is under colonial pressure",
    "Spain is not hostile to France"
  ],
  "forbidden_conditions": [
    "France does not control Louisiana",
    "Spain is hostile to France"
  ],
  "notes": "Historically attested, but should not fire unconditionally."
}
```

### CounterfactualContextAgent

Adds ahistorical but plausible fallback conditions.

Output should separate:

- historically attested context,
- counterfactual valid context,
- invalid context.

### DesignerAgent

Writes player-facing text:

- title,
- description,
- option text,
- tooltip text.

The DesignerAgent must not alter mechanics.

### ScriptReviewAgent

Reviews rendered or pre-rendered script structure for technical risks.

The primary renderer should still be deterministic.

## Rule-Based First

Implement rule-based agents before LLM agents.

Initial agents:

```text
RuleBasedHistoryAgent
RuleBasedCounterfactualAgent
TemplateDesignerAgent
```

Then add LLM-backed implementations behind the same interface.

## Agent Interface

```python
class Agent(Protocol):
    agent_name: str
    agent_version: str

    def review(self, request: AgentRequest) -> AgentReview:
        ...
```

## Persistence

Every agent call must be persisted:

```text
agent_name
agent_version
model_name
prompt_version
input_hash
output_json
verdict
created_at
```

This is required for reproducibility.

## Safety and Control

Agents may enrich specs, but only within allowed fields.

Bad:

```text
DesignerAgent changes event effects.
```

Good:

```text
DesignerAgent writes localization only.
HistoryAgent adds required constraints.
Renderer uses validated EventSpec.
```
