ALLOWED=("ADVANCE","WATCH","YIELD")
_MAP={"CLEAR_PROGRESS":"ADVANCE","UNCERTAIN_TRANSIENT":"WATCH","HARD_INVALIDATION":"YIELD"}
def select_disposition(state):
    out=_MAP.get(state)
    if out is None: raise ValueError('unknown typed local state')
    if out not in ALLOWED: raise RuntimeError('out-of-envelope')
    return out
