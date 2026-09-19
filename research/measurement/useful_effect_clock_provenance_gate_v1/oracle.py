def classify(e, acts):
    amap={}
    for a in acts:
        if type(a.actuation_id) is not str or a.actuation_id=='' or a.actuation_id in amap: raise ValueError('act id')
        if type(a.down_lo) is not int or type(a.down_hi) is not int or a.down_lo<0 or a.down_hi<a.down_lo: raise ValueError('act interval')
        amap[a.actuation_id]=a
    if type(e.effect_id) is not str or e.effect_id=='': return 'invalid_identity'
    if type(e.t_ns) is not int or e.t_ns<0: return 'invalid_temporal'
    if type(e.scored) is not bool or type(e.useful) is not bool: return 'invalid_identity'
    if e.scored is False: return 'unscored'
    if e.actuation_id is None or e.actuation_id not in amap:
        return 'useful_unbound' if e.useful else 'nonuseful_unbound'
    if type(e.actuation_id) is not str or e.actuation_id=='': return 'invalid_identity'
    a=amap[e.actuation_id]
    vals=(e.clock_domain,e.clock_epoch,a.clock_domain,a.clock_epoch)
    if any(type(v) is not str or v=='' for v in vals): return 'temporal_clock_unknown'
    if e.clock_domain!=a.clock_domain or e.clock_epoch!=a.clock_epoch: return 'temporal_clock_mismatch'
    # Independent endpoint reasoning: all admissible exact down times are integers in [lo,hi].
    before=[]
    for d in range(a.down_lo,a.down_hi+1): before.append(e.t_ns < d)
    if all(before): return 'invalid_temporal'
    if any(before): return 'temporal_ambiguous'
    return 'useful_bound' if e.useful else 'nonuseful_bound'

def parent988(e, acts):
    amap={a.actuation_id:a for a in acts}
    if type(e.effect_id) is not str or e.effect_id=='': return 'invalid_identity'
    if type(e.t_ns) is not int or e.t_ns<0: return 'invalid_temporal'
    if not e.scored: return 'unscored'
    if e.actuation_id is None or e.actuation_id not in amap: return 'useful_unbound' if e.useful else 'nonuseful_unbound'
    a=amap[e.actuation_id]
    if e.t_ns<a.down_lo:return 'invalid_temporal'
    if e.t_ns<a.down_hi:return 'temporal_ambiguous'
    return 'useful_bound' if e.useful else 'nonuseful_bound'
