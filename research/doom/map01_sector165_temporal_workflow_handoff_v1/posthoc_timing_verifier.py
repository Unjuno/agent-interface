from pathlib import Path
import argparse,json,statistics,hashlib

PAIRS=[('f00','f01'),('f03','f02'),('f05','f04'),('f06','f07')]

def load_case(root,cid):
    p=root/cid
    s=json.loads((p/'score.json').read_text())
    n=json.loads((p/'next_subgoal'/'result.json').read_text())
    errs=[]
    calc=(int(s['next_subgoal_release_done_ns'])-int(s['workflow_start_ns']))/1e6
    if abs(calc-float(s['workflow_release_elapsed_ms']))>1e-6:
        errs.append(f'{cid}: derived workflow elapsed mismatch stored={s["workflow_release_elapsed_ms"]} calc={calc}')
    if int(s['next_subgoal_release_done_ns'])!=int(n['release_done_ns']):
        errs.append(f'{cid}: score/next release_done mismatch')
    if not (int(s['workflow_start_ns']) < int(n['down_done_ns']) <= int(n['up_started_ns']) <= int(n['release_done_ns'])):
        errs.append(f'{cid}: next-subgoal timestamp ordering invalid')
    rel=n.get('release',{})
    if not rel.get('verified') or rel.get('keys_down') or rel.get('buttons_down'):
        errs.append(f'{cid}: next-subgoal release not verified neutral')
    return s,n,calc,errs

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--evidence',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    root=Path(a.evidence); errors=[]; rows={}; calcs={}
    for cid in [f'f{i:02d}' for i in range(12)]:
        s,n,calc,errs=load_case(root,cid);errors.extend(errs);rows[cid]=s;calcs[cid]=calc
    reductions=[calcs[e]-calcs[t] for e,t in PAIRS]
    gates={
        'timing_raw_ge200_ge3pairs':sum(x>=200 for x in reductions)>=3,
        'timing_raw_median_ge200':statistics.median(reductions)>=200,
    }
    if not all(gates.values()): errors.append(f'raw timing gate failed: {reductions}')
    result={
        'schema':'map01-sector165-temporal-workflow-handoff-posthoc-timing-verifier-v1',
        'status':'PASS_POSTHOC_RAW_TIMING_INTEGRITY' if not errors else 'FAIL_POSTHOC_RAW_TIMING_INTEGRITY',
        'errors':errors,
        'pair_reductions_ms_from_raw_timestamps':reductions,
        'median_reduction_ms_from_raw_timestamps':statistics.median(reductions),
        'gates':gates,
        'note':'Postformal integrity verifier only. It does not alter frozen audit or scientific disposition.'
    }
    Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(0 if not errors else 2)
if __name__=='__main__':main()
