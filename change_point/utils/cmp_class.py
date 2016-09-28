import numpy as np
from hopcroftkarp import HopcroftKarp


def conf_mat(correct_class, pred_class, ts, win_len):
    """
    - description: return confusion matrix as dictionary. Match pred_class to
    correct_class maximizing number of true positives. One change point can be
    matched only once. By now solved with maximum matching in bipartite graph:
    nodes of the left represents change points of correct_class and the nodes
    of the right represents change points of pred_class. Two nodes are
    connected if the distance between than is less or equal than win_len. In
    case of more than one solution with maximum matching is possible to select
    the solution with minimum distance between matched change points, but for
    that, the problem must be solved with dynamic programming or
    min-cost-max-flow.
    - arguments:
        - correct_class: list with ids indicating change points of correct
        classification
        - pred_class : list with ids indicating change points of predicted
        classification
        - win_len: correct_class[i] can be matched with pred_class[j] if
        abs(correct_class[i] - pred_class[j]) <= win_len
    """

    graph = {}
    for l in xrange(len(correct_class)):
        neigh = set()
        for r in xrange(len(pred_class)):
            if abs(correct_class[l] - pred_class[r]) <= win_len:
                neigh.add("r{}".format(r))
        graph["l{}".format(l)] = neigh
    max_match = HopcroftKarp(graph).maximum_matching()

    conf = {}
    conf["tp"] = len(max_match) / 2
    conf["fp"] = len(pred_class) - conf["tp"]
    conf["fn"] = len(correct_class) - conf["tp"]
    # tn = number of true not change points - number of wrong predicted change
    # points
    # tn = (number of points - number of true change points) - number of wrong
    # predicted change points
    conf["tn"] = len(ts.y) - len(correct_class) - conf["fp"]

    return conf


def f_beta_score(beta, conf):
    tp = conf["tp"]
    fp = conf["fp"]
    fn = conf["fn"]
    num = float((1 + beta ** 2) * tp)
    den = float((1 + beta ** 2) * tp + beta ** 2 * fn + fp)

    if np.isclose(den, 0.0):
        return None
    return num / den


def f_half_score(conf):
    return f_beta_score(0.5, conf)


def f_1_score(conf):
    return f_beta_score(1.0, conf)


def f_2_score(conf):
    return f_beta_score(2.0, conf)


def jcc(conf):
    """
    jaccard's coefficient of community
    """

    tp = conf["tp"]
    fp = conf["fp"]
    fn = conf["fn"]
    num = float(tp)
    den = float(tp + fp + fn)

    if np.isclose(den, 0.0):
        return None
    return num / den


def acc(conf):
    """
    accuracy
    """

    tp = conf["tp"]
    fp = conf["fp"]
    fn = conf["fn"]
    tn = conf["tn"]
    p = tp + fn
    n = fp + tn
    num = float(tp + tn)
    den = float(p + n)

    if np.isclose(den, 0.0):
        return None
    return num / den


def bacc(conf):
    """
    balanced accuracy
    """

    tp = conf["tp"]
    fp = conf["fp"]
    fn = conf["fn"]
    tn = conf["tn"]
    p = tp + fn
    n = fp + tn

    if np.isclose(p, 0.0) or np.isclose(n, 0.0):
        return None
    return (float(tp) / p + float(tn) / n) / 2.0
