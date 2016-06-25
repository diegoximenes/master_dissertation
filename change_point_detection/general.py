from hopcroftkarp import HopcroftKarp


def conf_mat(correct_class, pred_class, win_len):
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

    # is not clear if tn will be necessary
    conf = {}
    conf["tp"] = len(max_match) / 2
    conf["fp"] = len(pred_class) - conf["tp"]
    conf["fn"] - len(correct_class) - conf["tp"]

    return conf
