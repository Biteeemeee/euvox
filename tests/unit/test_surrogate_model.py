"""Unit tests for the surrogate package: encoder, model, acquisition, guided optimizer."""

from dataclasses import dataclass

import numpy as np
import pytest
from euvox.search_space import default_search_space_v1
from euvox.surrogate import ExtraTreesSurrogate, FeatureEncoder, SurrogateGuidedOptimizer, ucb_score

# ── Helpers ───────────────────────────────────────────────────────────────────


@dataclass
class FakeSample:
    score_total: float
    operation_vector: dict


def _make_storage_vector(space, values: list[float]) -> dict[str, float]:
    return {f"numeric_patch.{p.name}": v for p, v in zip(space.parameters, values, strict=True)}


# ── FeatureEncoder ────────────────────────────────────────────────────────────


def test_encoder_from_space_has_correct_names() -> None:
    space = default_search_space_v1()
    enc = FeatureEncoder.from_space(space)
    assert enc.parameter_names == [p.name for p in space.parameters]


def test_encoder_transform_storage_format() -> None:
    space = default_search_space_v1()
    enc = FeatureEncoder.from_space(space)
    vec = _make_storage_vector(space, [0.6, 0.7, 0.8, 0.9])
    arr = enc.transform(vec)
    assert arr.shape == (4,)
    assert list(arr) == pytest.approx([0.6, 0.7, 0.8, 0.9])


def test_encoder_transform_point_format() -> None:
    space = default_search_space_v1()
    enc = FeatureEncoder.from_space(space)
    point = {p.name: float(i) for i, p in enumerate(space.parameters)}
    arr = enc.transform_point(point)
    assert arr.shape == (4,)
    assert list(arr) == pytest.approx([0.0, 1.0, 2.0, 3.0])


def test_encoder_missing_key_defaults_to_zero() -> None:
    space = default_search_space_v1()
    enc = FeatureEncoder.from_space(space)
    arr = enc.transform({})
    assert (arr == 0.0).all()


def test_encoder_transform_batch_shape() -> None:
    space = default_search_space_v1()
    enc = FeatureEncoder.from_space(space)
    vecs = [_make_storage_vector(space, [1.0, 1.0, 1.0, 1.0]) for _ in range(5)]
    X = enc.transform_batch(vecs)
    assert X.shape == (5, 4)


# ── ExtraTreesSurrogate ───────────────────────────────────────────────────────


def _fit_surrogate(n: int = 20) -> tuple[ExtraTreesSurrogate, np.ndarray]:
    X = np.random.default_rng(42).uniform(0, 1, (n, 4))
    y = X[:, 0] * 0.5 + X[:, 1] * 0.3 + np.random.default_rng(0).normal(0, 0.01, n)
    s = ExtraTreesSurrogate(n_estimators=20, random_state=42)
    s.fit(X, y)
    return s, X


def test_surrogate_fit_and_predict_shape() -> None:
    s, X = _fit_surrogate()
    pred = s.predict(X[:3])
    assert pred.means.shape == (3,)
    assert pred.stds.shape == (3,)


def test_surrogate_predict_raises_when_unfitted() -> None:
    s = ExtraTreesSurrogate()
    with pytest.raises(RuntimeError):
        s.predict(np.zeros((1, 4)))


def test_surrogate_stds_nonnegative() -> None:
    s, X = _fit_surrogate()
    pred = s.predict(X)
    assert (pred.stds >= 0).all()


def test_surrogate_save_load_roundtrip(tmp_path) -> None:
    s, X = _fit_surrogate()
    path = tmp_path / "model.joblib"
    s.save(path)
    s2 = ExtraTreesSurrogate.load(path)
    pred1 = s.predict(X[:5])
    pred2 = s2.predict(X[:5])
    np.testing.assert_array_almost_equal(pred1.means, pred2.means)


# ── UCB acquisition ───────────────────────────────────────────────────────────


def test_ucb_score_formula() -> None:
    means = np.array([0.5, 0.3])
    stds = np.array([0.1, 0.2])
    scores = ucb_score(means, stds, kappa=2.0)
    assert scores[0] == pytest.approx(0.5 + 2.0 * 0.1)
    assert scores[1] == pytest.approx(0.3 + 2.0 * 0.2)


def test_ucb_higher_uncertainty_wins_equal_mean() -> None:
    means = np.array([0.5, 0.5])
    stds = np.array([0.1, 0.5])
    scores = ucb_score(means, stds)
    assert scores[1] > scores[0]


# ── SurrogateGuidedOptimizer ──────────────────────────────────────────────────


def _make_trained_optimizer(pool_size: int = 50) -> SurrogateGuidedOptimizer:
    s, _ = _fit_surrogate(n=30)
    space = default_search_space_v1()
    enc = FeatureEncoder.from_space(space)
    return SurrogateGuidedOptimizer(s, enc, pool_size=pool_size)


def test_guided_optimizer_returns_n_candidates() -> None:
    opt = _make_trained_optimizer()
    space = default_search_space_v1()
    results = opt.suggest([], space, n=4)
    assert len(results) == 4


def test_guided_optimizer_values_within_bounds() -> None:
    opt = _make_trained_optimizer()
    space = default_search_space_v1()
    for point in opt.suggest([], space, n=10):
        for p in space.parameters:
            assert p.min_val <= point[p.name] <= p.max_val


def test_guided_optimizer_selects_by_ucb() -> None:
    """The top candidate should have a higher UCB score than a random draw."""
    s, _ = _fit_surrogate(n=30)
    space = default_search_space_v1()
    enc = FeatureEncoder.from_space(space)
    opt = SurrogateGuidedOptimizer(s, enc, pool_size=100, kappa=2.0)

    top = opt.suggest([], space, n=1)[0]
    top_vec = enc.transform_point(top)
    top_pred = s.predict(top_vec.reshape(1, -1))
    top_score = float(ucb_score(top_pred.means, top_pred.stds, kappa=2.0)[0])

    rng = np.random.default_rng(99)
    random_vecs = rng.uniform(0, 1, (20, 4))
    random_preds = s.predict(random_vecs)
    random_scores = ucb_score(random_preds.means, random_preds.stds, kappa=2.0)

    # top should beat the mean of random candidates
    assert top_score >= float(random_scores.mean())
