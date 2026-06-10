import random
from dataclasses import dataclass, field


@dataclass
class ParameterSpec:
    name: str
    min_val: float
    max_val: float
    default: float


@dataclass
class SearchSpaceDefinition:
    version: str
    parameters: list[ParameterSpec] = field(default_factory=list)

    def random_point(self) -> dict[str, float]:
        return {p.name: random.uniform(p.min_val, p.max_val) for p in self.parameters}

    def clamp(self, point: dict[str, float]) -> dict[str, float]:
        result = {}
        for p in self.parameters:
            val = point.get(p.name, p.default)
            result[p.name] = max(p.min_val, min(p.max_val, val))
        return result


def default_search_space_v1() -> SearchSpaceDefinition:
    return SearchSpaceDefinition(
        version="v1",
        parameters=[
            ParameterSpec("war_cost_factor", 0.5, 2.0, 1.0),
            ParameterSpec("technology_cost", 0.5, 1.5, 1.0),
            ParameterSpec("stability_cost_modifier", 0.5, 2.0, 1.0),
            ParameterSpec("idea_cost", 0.5, 1.5, 1.0),
        ],
    )
