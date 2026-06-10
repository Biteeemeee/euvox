import numpy as np


def ucb_score(means: np.ndarray, stds: np.ndarray, kappa: float = 1.96) -> np.ndarray:
    """Upper Confidence Bound acquisition: mean + kappa * std."""
    return means + kappa * stds
