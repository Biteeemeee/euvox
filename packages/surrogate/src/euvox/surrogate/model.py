from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.ensemble import ExtraTreesRegressor


@dataclass
class SurrogatePrediction:
    means: np.ndarray
    stds: np.ndarray


class ExtraTreesSurrogate:
    """ExtraTrees regressor with per-tree uncertainty estimates."""

    def __init__(self, n_estimators: int = 100, random_state: int = 42) -> None:
        self._model = ExtraTreesRegressor(
            n_estimators=n_estimators,
            random_state=random_state,
        )
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self._model.fit(X, y)
        self._fitted = True

    def predict(self, X: np.ndarray) -> SurrogatePrediction:
        if not self._fitted:
            raise RuntimeError("Surrogate not fitted")
        tree_preds = np.stack(
            [tree.predict(X) for tree in self._model.estimators_], axis=1
        )
        return SurrogatePrediction(
            means=tree_preds.mean(axis=1),
            stds=tree_preds.std(axis=1),
        )

    def save(self, path: Path) -> None:
        import joblib

        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._model, path)

    @classmethod
    def load(cls, path: Path) -> "ExtraTreesSurrogate":
        import joblib

        obj = cls()
        obj._model = joblib.load(path)
        obj._fitted = True
        return obj
