from dataclasses import dataclass

@dataclass(frozen=True)
class Actuation:
    actuation_id: str
    down_lo: int
    down_hi: int
    clock_domain: str|None
    clock_epoch: str|None

@dataclass(frozen=True)
class Effect:
    effect_id: str
    actuation_id: str|None
    t_ns: int
    scored: bool
    useful: bool
    clock_domain: str|None
    clock_epoch: str|None


def _act_map(acts):
    out={}
    for a in acts:
        if not isinstance(a.actuation_id,str) or not a.actuation_id or a.actuation_id in out:
            raise ValueError('invalid actuation identity')
        if type(a.down_lo) is not int or type(a.down_hi) is not int or a.down_lo<0 or a.down_hi<a.down_lo:
            raise ValueError('invalid actuation interval')
        out[a.actuation_id]=a
    return out

def _prefix(effect):
    if not isinstance(effect.effect_id,str) or not effect.effect_id:
        return 'invalid_identity'
    if type(effect.t_ns) is not int or effect.t_ns < 0:
        return 'invalid_temporal'
    if type(effect.scored) is not bool or type(effect.useful) is not bool:
        return 'invalid_identity'
    if not effect.scored:
        return 'unscored'
    return None

def numeric_only(effect, acts):
    amap=_act_map(acts)
    p=_prefix(effect)
    if p: return p
    if effect.actuation_id is None or effect.actuation_id not in amap:
        return 'useful_unbound' if effect.useful else 'nonuseful_unbound'
    if not isinstance(effect.actuation_id,str) or not effect.actuation_id:
        return 'invalid_identity'
    a=amap[effect.actuation_id]
    if effect.t_ns < a.down_lo: return 'invalid_temporal'
    if effect.t_ns < a.down_hi: return 'temporal_ambiguous'
    return 'useful_bound' if effect.useful else 'nonuseful_bound'

def clock_bound(effect, acts):
    amap=_act_map(acts)
    p=_prefix(effect)
    if p: return p
    if effect.actuation_id is None or effect.actuation_id not in amap:
        return 'useful_unbound' if effect.useful else 'nonuseful_unbound'
    if not isinstance(effect.actuation_id,str) or not effect.actuation_id:
        return 'invalid_identity'
    a=amap[effect.actuation_id]
    cp=(effect.clock_domain,effect.clock_epoch,a.clock_domain,a.clock_epoch)
    if any(not isinstance(x,str) or not x for x in cp):
        return 'temporal_clock_unknown'
    if (effect.clock_domain,effect.clock_epoch)!=(a.clock_domain,a.clock_epoch):
        return 'temporal_clock_mismatch'
    if effect.t_ns < a.down_lo: return 'invalid_temporal'
    if effect.t_ns < a.down_hi: return 'temporal_ambiguous'
    return 'useful_bound' if effect.useful else 'nonuseful_bound'
