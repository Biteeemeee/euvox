from dataclasses import dataclass

import numpy as np
from euvox.search_space import SearchSpaceDefinition


@dataclass
class FeatureEncoder:
    """Maps operation vectors (numeric_patch.* keys) to fixed-length numpy arrays."""

    parameter_names: list[str]

    @classmethod
    def from_space(cls, space: SearchSpaceDefinition) -> "FeatureEncoder":
        return cls([p.name for p in space.parameters])

    def transform(self, vector: dict[str, float]) -> np.ndarray:
        """Accept storage-format vector: {"numeric_patch.<name>": value, ...}"""
        return np.array(
            [vector.get(f"numeric_patch.{name}", 0.0) for name in self.parameter_names],
            dtype=np.float64,
        )

    def transform_point(self, point: dict[str, float]) -> np.ndarray:
        """Accept optimizer-format point: {"<name>": value, ...}"""
        return np.array(
            [point.get(name, 0.0) for name in self.parameter_names],
            dtype=np.float64,
        )

    def transform_batch(self, vectors: list[dict[str, float]]) -> np.ndarray:
        return np.stack([self.transform(v) for v in vectors])

    def transform_points_batch(self, points: list[dict[str, float]]) -> np.ndarray:
        return np.stack([self.transform_point(p) for p in points])
