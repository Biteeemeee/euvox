"""Unit tests for optimizer candidate generation logic."""

from dataclasses import dataclass

from euvox.search_space import SearchSpaceDefinition, default_search_space_v1
from optimizer_service.optimizers import RandomSearchOptimizer, SimpleEvolutionaryOptimizer

# ── Helpers ───────────────────────────────────────────────────────────────────


@dataclass
class FakeSample:
    score_total: float
    operation_vector: dict


def _make_samples(n: int, base_score: float = 0.5) -> list[FakeSample]:
    space = default_search_space_v1()
    return [
        FakeSample(
            score_total=base_score + i * 0.01,
            operation_vector={f"numeric_patch.{p.name}": p.default for p in space.parameters},
        )
        for i in range(n)
    ]


# ── SearchSpaceDefinition ─────────────────────────────────────────────────────


def test_random_point_within_bounds() -> None:
    space = default_search_space_v1()
    for _ in range(20):
        point = space.random_point()
        for p in space.parameters:
            assert p.min_val <= point[p.name] <= p.max_val


def test_clamp_enforces_bounds() -> None:
    space = default_search_space_v1()
    extreme = {p.name: p.max_val * 10 for p in space.parameters}
    clamped = space.clamp(extreme)
    for p in space.parameters:
        assert clamped[p.name] == p.max_val


def test_default_search_space_v1_has_four_parameters() -> None:
    space = default_search_space_v1()
    assert len(space.parameters) == 4
    assert space.version == "v1"


# ── RandomSearchOptimizer ─────────────────────────────────────────────────────


def test_random_optimizer_returns_n_candidates() -> None:
    opt = RandomSearchOptimizer()
    space = default_search_space_v1()
    results = opt.suggest([], space, n=5)
    assert len(results) == 5


def test_random_optimizer_values_within_bounds() -> None:
    opt = RandomSearchOptimizer()
    space = default_search_space_v1()
    for point in opt.suggest([], space, n=10):
        for p in space.parameters:
            assert p.min_val <= point[p.name] <= p.max_val


def test_random_optimizer_ignores_samples() -> None:
    opt = RandomSearchOptimizer()
    space = default_search_space_v1()
    samples = _make_samples(100)
    # Should still work and not crash
    results = opt.suggest(samples, space, n=3)
    assert len(results) == 3


# ── SimpleEvolutionaryOptimizer ───────────────────────────────────────────────


def test_evolutionary_falls_back_to_random_below_threshold() -> None:
    opt = SimpleEvolutionaryOptimizer(population_size=10)
    space = default_search_space_v1()
    samples = _make_samples(5)
    results = opt.suggest(samples, space, n=3)
    assert len(results) == 3
    for point in results:
        for p in space.parameters:
            assert p.min_val <= point[p.name] <= p.max_val


def test_evolutionary_produces_n_candidates() -> None:
    opt = SimpleEvolutionaryOptimizer(population_size=5)
    space = default_search_space_v1()
    samples = _make_samples(10)
    results = opt.suggest(samples, space, n=4)
    assert len(results) == 4


def test_evolutionary_output_within_bounds() -> None:
    opt = SimpleEvolutionaryOptimizer(population_size=5, mutation_stddev=0.5)
    space = default_search_space_v1()
    samples = _make_samples(10)
    for point in opt.suggest(samples, space, n=20):
        for p in space.parameters:
            assert p.min_val <= point[p.name] <= p.max_val


def test_evolutionary_prefers_high_score_parents() -> None:
    """High-scoring samples should dominate tournament selection."""
    opt = SimpleEvolutionaryOptimizer(
        population_size=5, mutation_stddev=0.0, tournament_k=5
    )
    space = SearchSpaceDefinition(
        version="v1",
        parameters=[],
    )
    # With stddev=0 and no parameters, all suggestions are empty dicts
    from euvox.search_space.definition import ParameterSpec

    space.parameters = [ParameterSpec("x", 0.0, 1.0, 0.5)]

    best_val = 0.9
    samples = [
        FakeSample(score_total=0.1, operation_vector={"numeric_patch.x": 0.1}),
        FakeSample(score_total=0.1, operation_vector={"numeric_patch.x": 0.1}),
        FakeSample(score_total=0.1, operation_vector={"numeric_patch.x": 0.1}),
        FakeSample(score_total=0.1, operation_vector={"numeric_patch.x": 0.1}),
        FakeSample(score_total=best_val, operation_vector={"numeric_patch.x": best_val}),
    ]

    results = opt.suggest(samples, space, n=10)
    # With mutation_stddev=0 and tournament_k=5 (all 5 sampled), best parent always wins
    for r in results:
        assert abs(r["x"] - best_val) < 1e-9
