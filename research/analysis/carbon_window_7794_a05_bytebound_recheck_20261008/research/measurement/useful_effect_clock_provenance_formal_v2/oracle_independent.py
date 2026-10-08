# Independently structured oracle. Does not import candidate classification logic.
def classify(effect, acts):
    by_id={}
    for a in acts:
        if type(a.actuation_id) is not str or a.actuation_id == '' or a.actuation_id in by_id:
            raise ValueError('actuation identity')
        if type(a.down_lo) is not int or type(a.down_hi) is not int or a.down_lo < 0 or a.down_hi < a.down_lo:
            raise ValueError('actuation interval')
        by_id[a.actuation_id]=a
    if type(effect.effect_id) is not str or effect.effect_id == '':
        return 'invalid_identity'
    if type(effect.t_ns) is not int or effect.t_ns < 0:
        return 'invalid_temporal'
    if type(effect.scored) is not bool or type(effect.useful) is not bool:
        return 'invalid_identity'
    if effect.scored is False:
        return 'unscored'
    if effect.actuation_id is None or effect.actuation_id not in by_id:
        return 'useful_unbound' if effect.useful else 'nonuseful_unbound'
    a=by_id[effect.actuation_id]
    vals=[effect.clock_domain,effect.clock_epoch,a.clock_domain,a.clock_epoch]
    if any(type(v) is not str or v == '' for v in vals):
        return 'temporal_clock_unknown'
    if effect.clock_domain != a.clock_domain or effect.clock_epoch != a.clock_epoch:
        return 'temporal_clock_mismatch'
    flags=[effect.t_ns < d for d in range(a.down_lo,a.down_hi+1)]
    if all(flags):
        return 'invalid_temporal'
    if any(flags):
        return 'temporal_ambiguous'
    return 'useful_bound' if effect.useful else 'nonuseful_bound'

def parent988(effect, acts):
    by_id={a.actuation_id:a for a in acts}
    if type(effect.effect_id) is not str or effect.effect_id == '': return 'invalid_identity'
    if type(effect.t_ns) is not int or effect.t_ns < 0: return 'invalid_temporal'
    if effect.scored is False: return 'unscored'
    if effect.actuation_id is None or effect.actuation_id not in by_id:
        return 'useful_unbound' if effect.useful else 'nonuseful_unbound'
    a=by_id[effect.actuation_id]
    if effect.t_ns < a.down_lo: return 'invalid_temporal'
    if effect.t_ns < a.down_hi: return 'temporal_ambiguous'
    return 'useful_bound' if effect.useful else 'nonuseful_bound'
