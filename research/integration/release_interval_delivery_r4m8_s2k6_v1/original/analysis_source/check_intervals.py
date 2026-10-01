"""Finite analytical check only. No GUI, model, backend or network imports."""
from __future__ import annotations
import itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'source'))
from witness import estimate

def guarded(samples,ctx,key,deadline):
    result=estimate(samples,ctx,key,deadline)
    interval=result['interval_ns']
    if interval is not None and interval[0]>=interval[1]:
        return {'status':'UNKNOWN','authority':'none','task_success':False,'interval_ns':None,
                'reason':'empty_release_interval'}
    return result

def main():
    output=Path(sys.argv[1]);output.mkdir(parents=True,exist_ok=False)
    rows=[]
    for i,t in enumerate(itertools.combinations_with_replacement(range(9),4)):
        a,b,c,d=[10+x for x in t];ctx={'case_id':f'finite-{i:03}','server_epoch':'analytical-not-a-display'}
        samples=[]
        for j,(start,end,state) in enumerate([(0,1,False),(a,b,True),(c,d,False)]):
            bits=bytearray(32)
            if state:bits[8]=1
            samples.append(dict(ctx,sequence=j,start_ns=start,end_ns=end,keycode=64,bitmap_hex=bits.hex()))
        rows.append({'id':i,'bounds_ns':[a,b,c,d],'deadline_ns':d,'context':ctx,'samples':samples,
                     'original_local_estimator':estimate(samples,ctx,64,d),
                     'nonempty_guard':guarded(samples,ctx,64,d),
                     'return_lower_comparator':[b,d], 'request_upper_comparator':[a,c]})
    (output/'RAW.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'rows':len(rows),'kind':'finite_analytical_verification','live_trials':0,'authority':'none'},sort_keys=True))
if __name__=='__main__':main()
