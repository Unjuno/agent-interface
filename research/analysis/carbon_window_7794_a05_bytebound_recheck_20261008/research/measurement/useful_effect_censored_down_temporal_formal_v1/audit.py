from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
PARENT=HERE.parent/'useful_effect_censored_down_temporal_v1'
sys.path.insert(0,str(PARENT)); sys.path.insert(0,str(HERE))
from candidate import *
from corpus import generate,STRATA
import oracle

CANDIDATE_SHA256='58ec7ac9f8f2115aceec42236f42e2cdbb298d2fd1a0f7824e096474a47edb0f'
FORMAL_SEED=98420260917002
FORMAL_PER_STRATUM=25000

def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def audit(path,seed=FORMAL_SEED,per=FORMAL_PER_STRATUM):
    r=json.loads(Path(path).read_text()); errors=[]
    if h(PARENT/'candidate.py')!=CANDIDATE_SHA256: errors.append('candidate_source_drift')
    if r.get('formal_seed')!=seed:errors.append('seed')
    if r.get('per_stratum')!=per:errors.append('per_stratum')
    if r.get('formal_invocations')!=1 or r.get('formal_reruns')!=0:errors.append('invocation')
    digest=hashlib.sha256(); mismatches=0; exact_parent_mismatch=0; ambiguous_promotions=0; occ_mismatch=0; precedence_mismatch=0
    totals={s:{k:0 for k in BUCKETS} for s in STRATA}; cases=0; records=0
    for idx,stratum,wait,acts,ers in generate(seed,per):
        got=analyze(wait,acts,ers); want=oracle.effects(ers,acts); occ=oracle.occupancy(wait,acts)
        if got['effects']!=want:mismatches+=1
        if got['occupancy']!=occ:occ_mismatch+=1
        if analyze(wait,acts,[])['occupancy']!=occ:occ_mismatch+=1
        if stratum=='EXACT_DOWN':
            if got['effects']['temporal_ambiguous']!=0: exact_parent_mismatch+=1
            # Compare each record against exact parent disposition where lineage binds one actuation.
            by={a.actuation_id:a for a in acts}
            for er in ers:
                a=by.get(er.event.actuation_id)
                if a is not None and a.down_lo==a.down_hi:
                    cr=oracle.role(er.event,acts); pr=oracle.exact_parent_role(er.event,a)
                    if cr!=pr: exact_parent_mismatch+=1
        for er in ers:
            orole=oracle.role(er.event,acts)
            if orole=='temporal_ambiguous':
                # candidate per-record classification
                one=analyze(wait,acts,[EffectRecord('only',er.event)])['effects']
                if one['useful_bound'] or one['nonuseful_bound']: ambiguous_promotions+=1
        if stratum=='PRECEDENCE_STRESS' and got['effects']!=want: precedence_mismatch+=1
        for k,v in got['effects'].items():totals[stratum][k]+=v
        records+=len(ers);cases+=1
        digest.update(json.dumps([idx,stratum,got],sort_keys=True,separators=(',',':')).encode())
    if mismatches:errors.append('effect_oracle')
    if occ_mismatch:errors.append('occupancy')
    if exact_parent_mismatch:errors.append('parent_degeneration')
    if ambiguous_promotions:errors.append('ambiguous_promotion')
    if precedence_mismatch:errors.append('precedence')
    if r.get('formal_cases')!=cases or cases!=4*per:errors.append('case_count')
    if r.get('formal_records')!=records:errors.append('record_count')
    if r.get('candidate_digest_sha256')!=digest.hexdigest():errors.append('digest')
    if r.get('bucket_totals_by_stratum')!=totals:errors.append('bucket_totals')
    if r.get('exact_down_ambiguous')!=0:errors.append('formal_exact_ambiguous')
    if r.get('occupancy_effect_mutations')!=0:errors.append('formal_occupancy_mutation')
    if r.get('fixed_malformed_controls_passed')!=8:errors.append('controls')
    return {'errors':errors,'candidate_oracle_mismatches':mismatches,'occupancy_mismatches':occ_mismatch,'exact_parent_mismatches':exact_parent_mismatch,'ambiguous_to_bound_promotions':ambiguous_promotions,'precedence_mismatches':precedence_mismatch,'audited_cases':cases,'audited_records':records,'digest_sha256':digest.hexdigest()}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--preflight',action='store_true');args=ap.parse_args()
    seed=98820260917000 if args.preflight else FORMAL_SEED;per=250 if args.preflight else FORMAL_PER_STRATUM
    print(json.dumps(audit(args.result,seed,per),indent=2,sort_keys=True))
if __name__=='__main__':main()
