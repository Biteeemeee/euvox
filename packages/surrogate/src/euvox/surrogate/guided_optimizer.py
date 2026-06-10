from euvox.search_space import SearchSpaceDefinition
from euvox.surrogate.acquisition import ucb_score
from euvox.surrogate.encoder import FeatureEncoder
from euvox.surrogate.model import ExtraTreesSurrogate


class SurrogateGuidedOptimizer:
    """Samples a large random pool, ranks by UCB, returns the top-n candidates."""

    def __init__(
        self,
        surrogate: ExtraTreesSurrogate,
        encoder: FeatureEncoder,
        pool_size: int = 200,
        kappa: float = 1.96,
    ) -> None:
        self.surrogate = surrogate
        self.encoder = encoder
        self.pool_size = pool_size
        self.kappa = kappa

    def suggest(
        self, samples: list, space: SearchSpaceDefinition, n: int = 1
    ) -> list[dict[str, float]]:
        pool = [space.random_point() for _ in range(self.pool_size)]
        X = self.encoder.transform_points_batch(pool)
        pred = self.surrogate.predict(X)
        scores = ucb_score(pred.means, pred.stds, self.kappa)


        top_indices = list(map(int, scores.argsort()[::-1][:n]))
        return [pool[i] for i in top_indices]
