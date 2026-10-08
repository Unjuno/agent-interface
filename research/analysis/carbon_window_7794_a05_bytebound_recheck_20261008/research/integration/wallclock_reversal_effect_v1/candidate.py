from __future__ import annotations

SPEED_PX_S = 73.0
DISP_ERROR_BOUND_PX = 2.0
FRESHNESS_NS = 150_000_000


def _full_sign(d: float, expected: float):
    pos = abs(d - expected) <= DISP_ERROR_BOUND_PX
    neg = abs(d + expected) <= DISP_ERROR_BOUND_PX
    if pos == neg:
        return None
    return 1 if pos else -1


def decide(records, *, session_id: str, window_id: int):
    if not isinstance(records, list) or len(records) != 3:
        return {'decision':'UNKNOWN','reason':'INVALID_RECORD_COUNT','authority':'none'}
    try:
        epochs=[r['epoch'] for r in records]
        times=[r['source_ns'] for r in records]
        xs=[float(r['x']) for r in records]
    except Exception:
        return {'decision':'UNKNOWN','reason':'INVALID_RECORD','authority':'none'}
    if len(set(epochs)) != 1:
        return {'decision':'UNKNOWN','reason':'CROSS_EPOCH_SOURCE','authority':'none'}
    if not (times[0] > times[1] > times[2]):
        return {'decision':'UNKNOWN','reason':'DUPLICATE_OR_NONMONOTONIC_SOURCE','authority':'none'}
    dt_new=(times[0]-times[1])/1e9
    dt_prev=(times[1]-times[2])/1e9
    if dt_new <= 0 or dt_prev <= 0:
        return {'decision':'UNKNOWN','reason':'DUPLICATE_OR_NONMONOTONIC_SOURCE','authority':'none'}
    s_new=_full_sign(xs[0]-xs[1], SPEED_PX_S*dt_new)
    s_prev=_full_sign(xs[1]-xs[2], SPEED_PX_S*dt_prev)
    pred=0
    reason='NO_FULL_INTERVAL'
    if s_new is not None:
        if s_prev == s_new:
            pred=0; reason='SAME_DIRECTION_INTERVALS'
        else:
            pred=s_new; reason='NEWEST_FULL_INTERVAL'
    elif s_prev is not None:
        pred=-s_prev; reason='REVERSAL_IN_NEWEST_INTERVAL'
    return {
        'decision': 'RIGHT' if pred == 1 else 'LEFT' if pred == -1 else 'UNKNOWN',
        'direction': pred,
        'reason': reason,
        'source_epoch': epochs[0],
        'session_id': session_id,
        'window_id': int(window_id),
        'authority':'none',
    }


def admit(decision, *, now_ns: int, decision_created_ns: int,
          session_id: str, epoch: str, window_id: int):
    if decision.get('decision') not in ('LEFT','RIGHT'):
        return {'admitted':False,'reason':'UNKNOWN_OR_REFUSED','authority':'none'}
    if now_ns - decision_created_ns > FRESHNESS_NS or now_ns < decision_created_ns:
        return {'admitted':False,'reason':'STALE_DECISION','authority':'none'}
    if (decision.get('session_id') != session_id or decision.get('source_epoch') != epoch
            or decision.get('window_id') != int(window_id)):
        return {'admitted':False,'reason':'BINDING_MISMATCH','authority':'none'}
    return {'admitted':True,'reason':'ADMITTED_FRESH_BOUND','direction':decision['direction'],'authority':'none'}
