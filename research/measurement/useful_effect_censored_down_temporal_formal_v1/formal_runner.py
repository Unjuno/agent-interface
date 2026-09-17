from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
PARENT=HERE.parent/'useful_effect_censored_down_temporal_v1'
sys.path.insert(0,str(PARENT)); sys.path.insert(0,str(HERE))
from candidate import *
from corpus import generate,STRATA

CANDIDATE_SHA256='58ec7ac9f8f2115aceec42236f42e2cdbb298d2fd1a0f7824e096474a47edb0f'
FORMAL_SEED=98420260917002
FORMAL_PER_STRATUM=25000

def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def controls():
    ok=0
    def rejects(fn):
        nonlocal ok
        try: fn()
        except (ValueError,TypeError): ok+=1; return
        raise AssertionError('malformed control accepted')
    rejects(lambda: Actuation('',1,1,2,2))
    rejects(lambda: Actuation(0,1,1,2,2))
    rejects(lambda: analyze(Interval(0,10),[Actuation('a',1,1,2,2),Actuation('a',3,3,4,4)],[]))
    rejects(lambda: analyze(Interval(0,10),[Actuation('a',1,1,2,2)],[EffectRecord('',Event(2,'a',True,True))]))
    rejects(lambda: analyze(Interval(0,10),[Actuation('a',1,1,2,2)],[EffectRecord('e',Event(2,'a',True,True)),EffectRecord('e',Event(3,'a',True,True))]))
    rejects(lambda: Actuation('a',4,3,5,6))
    rejects(lambda: Actuation('a',2,4,3,6))
    rejects(lambda: Interval(5,4))
    return ok

def run(seed,per,out):
    if out.exists(): raise RuntimeError('exclusive formal output already exists')
    if sha256(PARENT/'candidate.py')!=CANDIDATE_SHA256: raise RuntimeError('candidate source drift')
    digest=hashlib.sha256(); totals={s:{k:0 for k in BUCKETS} for s in STRATA}
    exact_ambiguous=0; occupancy_effect_mutation=0; cases=0; records=0
    for idx,stratum,wait,acts,ers in generate(seed,per):
        got=analyze(wait,acts,ers)
        base=analyze(wait,acts,[])
        occupancy_effect_mutation += got['occupancy']!=base['occupancy']
        exact_ambiguous += got['effects']['temporal_ambiguous'] if stratum=='EXACT_DOWN' else 0
        for k,v in got['effects'].items(): totals[stratum][k]+=v
        records += len(ers); cases+=1
        digest.update(json.dumps([idx,stratum,got],sort_keys=True,separators=(',',':')).encode())
    result={
      'task':'USEFUL-EFFECT-CENSORED-DOWN-TEMPORAL-FORMAL-20260917-002',
      'candidate_sha256':CANDIDATE_SHA256,'formal_seed':seed,'per_stratum':per,
      'formal_cases':cases,'formal_records':records,'formal_invocations':1,'formal_reruns':0,
      'fixed_malformed_controls_passed':controls(),'exact_down_ambiguous':exact_ambiguous,
      'occupancy_effect_mutations':occupancy_effect_mutation,'bucket_totals_by_stratum':totals,
      'candidate_digest_sha256':digest.hexdigest()
    }
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); ap.add_argument('--preflight',action='store_true'); args=ap.parse_args()
    seed=98820260917000 if args.preflight else FORMAL_SEED
    per=250 if args.preflight else FORMAL_PER_STRATUM
    print(json.dumps(run(seed,per,Path(args.out)),sort_keys=True))
if __name__=='__main__': main()
