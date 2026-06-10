from typing import Protocol, runtime_checkable

from euvox.agent_protocol.schemas import AgentReview, EventProposal


@runtime_checkable
class Agent(Protocol):
    name: str
    version: str

    def review(self, proposal: EventProposal) -> AgentReview: ...
