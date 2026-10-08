import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
EXP={'weighted_deficit_us':153403,'min_pure_width_reduction_us':38351,'min_lower_fixed_upper_inward_us':51135}
def main():
    r=json.loads((ROOT/'RESULT.json').read_text()); errs=[]
    if r.get('formal_invocations')!=1 or r.get('reruns')!=0: errs.append('invocation')
    if r.get('mismatches')!=0 or r.get('random_rows')!=250000: errs.append('corpus')
    if not all(r.get('controls',{}).values()): errs.append('controls')
    if r.get('v38',{}).get('zero_pass') is not True or r.get('v39',{}).get('zero_pass') is not False: errs.append('retained_points')
    for k,v in EXP.items():
        if r.get('v39',{}).get(k)!=v: errs.append(k)
    if r.get('decision')!='PASS_OCCUPANCY_GATE_FRONTIER_SCOPED' or r.get('pass') is not True: errs.append('decision')
    out={'pass':not errs,'errors':errs,'decision':r.get('decision') if not errs else 'FAIL_INTEGRITY',
         'result_sha256':hashlib.sha256((ROOT/'RESULT.json').read_bytes()).hexdigest()}
    (ROOT/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if not errs else 1)
if __name__=='__main__': main()
