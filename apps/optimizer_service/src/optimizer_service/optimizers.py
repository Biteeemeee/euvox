import random
from typing import Protocol, runtime_checkable

from euvox.search_space import SearchSpaceDefinition


@runtime_checkable
class CandidateOptimizer(Protocol):
    def suggest(
        self, samples: list, space: SearchSpaceDefinition, n: int = 1
    ) -> list[dict[str, float]]: ...


class RandomSearchOptimizer:
    def suggest(
        self, samples: list, space: SearchSpaceDefinition, n: int = 1
    ) -> list[dict[str, float]]:
        return [space.random_point() for _ in range(n)]


class SimpleEvolutionaryOptimizer:
    """Tournament selection + Gaussian mutation over the top population_size samples."""

    def __init__(
        self,
        population_size: int = 10,
        mutation_stddev: float = 0.1,
        tournament_k: int = 3,
    ) -> None:
        self.population_size = population_size
        self.mutation_stddev = mutation_stddev
        self.tournament_k = tournament_k

    def suggest(
        self, samples: list, space: SearchSpaceDefinition, n: int = 1
    ) -> list[dict[str, float]]:
        if len(samples) < self.population_size:
            return RandomSearchOptimizer().suggest(samples, space, n)

        elite = sorted(samples, key=lambda s: s.score_total, reverse=True)[: self.population_size]

        results = []
        for _ in range(n):
            tournament = random.sample(elite, min(self.tournament_k, len(elite)))
            parent = max(tournament, key=lambda s: s.score_total)
            parent_vec: dict[str, object] = dict(parent.operation_vector)

            mutated: dict[str, float] = {}
            for p in space.parameters:
                base = float(parent_vec.get(f"numeric_patch.{p.name}", p.default))
                noise = random.gauss(0.0, self.mutation_stddev * (p.max_val - p.min_val))
                mutated[p.name] = max(p.min_val, min(p.max_val, base + noise))

            results.append(mutated)

        return results
