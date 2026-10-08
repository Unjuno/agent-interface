"""Finite same-clock membership model, not an input-authority implementation."""
def classify(edges, effect, cause):
    if len(edges) != 4 or any(type(x) is not int for x in edges):
        raise ValueError('integer edge bounds required')
    dl, dh, rl, rh = edges
    if dl > dh or rl > rh or dl > rh:
        raise ValueError('empty or infeasible edge domain')
    if cause not in ('ACTION', 'ENVIRONMENT'):
        raise ValueError('unsupported causal evidence')
    if effect is not None and type(effect) is not int:
        raise ValueError('integer effect time required')
    if cause != 'ACTION' or effect is None:
        return 'F'
    if dh <= effect < rl:
        return 'T'
    if dl <= effect < rh:
        return 'U'
    return 'F'
