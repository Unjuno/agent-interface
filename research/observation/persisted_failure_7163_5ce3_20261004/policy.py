"""Persisted observed failure; deliberately test whether one envelope suffices."""
import json
FIELDS=('cover','geometry','focus','pending','business')
def learn(path,target,action,observed,failed_field,evidence):
    if failed_field not in FIELDS or observed.get(failed_field) is not False:
        raise ValueError('unobserved failure condition')
    with path.open('x') as f:
        json.dump(dict(target=target,attempted_action=action,observed_preconditions=observed,
                       outcome='NOT_COMMITTED',evidence=evidence,
                       applicability_envelope={'field':failed_field,'value':False},
                       invalidators=['target_changed','action_changed','missing_current_field'],
                       causal_hypothesis='author-seeded class; not learned cause'),f,sort_keys=True)
def decide(arm,path,observed,target,action):
    if arm=='NO_MEMORY':return 'TRY'
    if arm=='NOTE':return 'BLOCK'
    if arm=='FRESH':fields=FIELDS
    else:
        record=json.loads(path.read_text())
        if record['target']!=target or record['attempted_action']!=action:return 'UNKNOWN'
        fields=FIELDS if arm=='TYPED_PLUS_FRESH' else (record['applicability_envelope']['field'],)
    if any(type(observed.get(k)) is not bool for k in fields):return 'UNKNOWN'
    return 'TRY' if all(observed[k] for k in fields) else 'BLOCK'
