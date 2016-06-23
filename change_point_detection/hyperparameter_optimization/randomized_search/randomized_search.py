from sklearn.base import BaseEstimator


class SegmentNeighbourhood(BaseEstimator):
    def __init__(self):
        pass

    def get_params(self, deep=True):
        return {"penalization": self.penalization}

    def set_params(self, **params):
        for param, val in params.items():
            self.setattr(param, val)
        return self

    def fit(self, x, y):
        pass

    def score(self, x, y):
        pass
