import itertools, json, hashlib, argparse
from pathlib import Path

EVENTS=('KEY_PRESS','KEY_RELEASE','POINTER')
EFFECTS=('TEXT_CHANGE','FOCUS_CHANGE','GEOMETRY_CHANGE','NOOP_VISIBLE')
TIMING=('LT5MS','5_50MS','50_500MS','GT500MS')
FOCUS=(False,True)
DIGEST=('D0','D1','D2','D3')
ACTORS=('HUMAN','EXTERNAL_PROCESS')


def observable(event,effect,timing,focus,digest):
    return {'event_family':event,'effect_class':effect,'timing_bucket':timing,
            'focus_owned':focus,'state_digest_class':digest}

def encode(o):
    return json.dumps(o,sort_keys=True,separators=(',',':')).encode()

def heuristics(name,o):
    if name=='TIMING': return 'HUMAN' if o['timing_bucket'] in ('50_500MS','GT500MS') else 'EXTERNAL_PROCESS'
    if name=='EVENT_SHAPE': return 'HUMAN' if o['event_family']=='POINTER' else 'EXTERNAL_PROCESS'
    if name=='FOCUS': return 'HUMAN' if not o['focus_owned'] else 'EXTERNAL_PROCESS'
    if name=='EFFECT_SHAPE': return 'HUMAN' if o['effect_class']=='FOCUS_CHANGE' else 'EXTERNAL_PROCESS'
    if name=='COMPOSITE': return 'HUMAN' if (o['event_family']=='POINTER') ^ o['focus_owned'] else 'EXTERNAL_PROCESS'
    if name=='UNATTRIBUTED': return 'UNATTRIBUTED'
    raise ValueError(name)

def with_witness(o,actor):
    x=dict(o); x['trusted_actor_witness']={'actor_class':actor,'binding':'exact'}; return x

def classify_with_witness(x):
    w=x.get('trusted_actor_witness')
    return w['actor_class'] if isinstance(w,dict) and w.get('binding')=='exact' and w.get('actor_class') in ACTORS else 'UNATTRIBUTED'

def run():
    names=('TIMING','EVENT_SHAPE','FOCUS','EFFECT_SHAPE','COMPOSITE','UNATTRIBUTED')
    stats={n:{'errors':0,'false_specific_claims':0,'pair_specific_error_min':2} for n in names}
    pairs=0; histories=0; identical_pairs=0; witness_pairs_separated=0; witness_errors=0
    pair_hash=hashlib.sha256()
    for vals in itertools.product(EVENTS,EFFECTS,TIMING,FOCUS,DIGEST):
        o=observable(*vals); b=encode(o); pairs+=1; histories+=2; pair_hash.update(b)
        human_bytes=b; process_bytes=encode(observable(*vals))
        if human_bytes==process_bytes: identical_pairs+=1
        for n in names:
            y=heuristics(n,o)
            errs=int(y!='HUMAN')+int(y!='EXTERNAL_PROCESS')
            stats[n]['errors']+=errs
            stats[n]['pair_specific_error_min']=min(stats[n]['pair_specific_error_min'],errs)
            if y in ACTORS: stats[n]['false_specific_claims']+=errs
        wh=with_witness(o,'HUMAN'); wp=with_witness(o,'EXTERNAL_PROCESS')
        yh=classify_with_witness(wh); yp=classify_with_witness(wp)
        if yh=='HUMAN' and yp=='EXTERNAL_PROCESS': witness_pairs_separated+=1
        witness_errors += int(yh!='HUMAN')+int(yp!='EXTERNAL_PROCESS')
    specific=[n for n in names if n!='UNATTRIBUTED']
    decision='PASS_PROVENANCE_FREE_ACTOR_INDISTINGUISHABILITY_SCOPED'
    errors=[]
    if pairs!=384 or histories!=768: errors.append('cardinality')
    if identical_pairs!=pairs: errors.append('not_observationally_equivalent')
    if any(stats[n]['errors']<pairs for n in specific): errors.append('specific_classifier_not_forced_wrong_per_pair')
    if stats['UNATTRIBUTED']['false_specific_claims']!=0: errors.append('unattributed_false_specific')
    if witness_pairs_separated!=pairs or witness_errors!=0: errors.append('trusted_witness_not_separating')
    if errors: decision='FAIL_LOGIC_INTEGRITY'
    result={'decision':decision,'pairs':pairs,'histories':histories,'identical_observable_pairs':identical_pairs,
            'heuristics':stats,'trusted_witness_pairs_separated':witness_pairs_separated,'trusted_witness_errors':witness_errors,
            'authority_promotions':0,'task_success_promotions':0,'formal_invocations':1,'reruns':0,
            'observable_space_digest':pair_hash.hexdigest(),'errors':errors}
    return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); a=ap.parse_args(); p=Path(a.output)
    if p.exists(): raise SystemExit('output exists')
    r=run(); raw=json.dumps(r,sort_keys=True,separators=(',',':')).encode(); r['result_digest']=hashlib.sha256(raw).hexdigest()
    p.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__': main()
