"""Research-only projection of inherited cancellation, not OS input authority.

The caller owns a trusted complete ordered root-to-leaf registration at suspension.
Current records come from one coherent cooperative app snapshot. Local flags are
per frame; only task liveness and observation identity are inherited here. Other
ancestor predicates govern their OWN future continuation, not the child's.
"""
from __future__ import annotations
import json
import strict_policy

POLICIES=('LOCAL_FRAME','ALL_ANCESTOR_GATES','ANCESTOR_LIVENESS')
MAX_BYTES=65536
MAX_DEPTH=8

def result(verdict, leaf=None, checked=()):
    return {'verdict':verdict,'eligible':verdict=='RESUME','input_authority':False,
            'checked_frame_id':leaf,'checked_ancestors':list(checked)}

def decide_json(raw: bytes, policy: str) -> dict:
    if policy not in POLICIES:
        raise ValueError('unknown research policy')
    if type(raw) is not bytes or len(raw)>MAX_BYTES:
        return result('YIELD_MALFORMED')
    try:
        q=json.loads(raw.decode('utf-8','strict'),
                     object_pairs_hook=strict_policy._unique_object,
                     parse_constant=strict_policy._no_constant)
        if type(q) is not dict or set(q)!={'saved_chain','current_chain','leaf_level'}:
            return result('YIELD_MALFORMED')
        old,cur,level=q['saved_chain'],q['current_chain'],q['leaf_level']
        if type(level) is not int or not 0<=level<MAX_DEPTH:
            return result('YIELD_MALFORMED')
        if any(type(x) is not list or not 1<=len(x)<=MAX_DEPTH for x in (old,cur)):
            return result('YIELD_MALFORMED')
        if any(not strict_policy._valid_receipt(r) for chain in (old,cur) for r in chain):
            return result('YIELD_MALFORMED')
        if [r['level'] for r in old]!=list(range(level+1)):
            return result('YIELD_REGISTRATION')
        if len({r['level'] for r in cur})!=len(cur):
            return result('YIELD_MALFORMED')
        bylevel={r['level']:r for r in cur}; leaf=old[-1]['frame_id']
        if level not in bylevel:
            return result('YIELD_LEAF_MISSING',leaf)
        local=strict_policy.decide(old[-1],bylevel[level])
        if local['verdict']!='RESUME':
            return result(local['verdict'],leaf)
        if policy=='LOCAL_FRAME':
            return result('RESUME',leaf)
        if set(bylevel)!=set(range(level+1)):
            return result('YIELD_ANCESTRY_INCOMPLETE',leaf)
        checked=[]
        for i in range(level):
            s,c=old[i],bylevel[i]
            if (s['session']!=old[-1]['session'] or
                any(s[k]!=c[k] for k in ('session','frame_id','level'))):
                return result('YIELD_ANCESTRY_SCOPE',leaf,checked)
            checked.append(c['frame_id'])
            if not c['source_fresh'] or s['source_generation']!=c['source_generation']:
                return result('YIELD_ANCESTRY_STALE',leaf,checked)
            if c['task_active'] is False:
                return result('CANCELED_ANCESTOR',leaf,checked)
        if policy=='ALL_ANCESTOR_GATES':
            for i in range(level):
                ancestor=strict_policy.decide(old[i],bylevel[i])
                if ancestor['verdict']!='RESUME':
                    return result('ANCESTOR_'+ancestor['verdict'],leaf,checked)
        return result('RESUME',leaf,checked)
    except (ValueError,TypeError,UnicodeError,RecursionError,OverflowError):
        return result('YIELD_MALFORMED')
