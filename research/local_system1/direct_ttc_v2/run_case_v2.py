#!/usr/bin/env python3
import os
for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[k]='1'
import argparse,json,resource,sys
from pathlib import Path
import numpy as np, torch
sys.path.insert(0,str(Path(__file__).parent))
import run_direct_ttc_v1 as v1
SEEDS=[9061701,9061702,9061703,9061704]

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--seed',type=int,required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
 if a.seed not in SEEDS: raise SystemExit('invalid frozen seed')
 torch.set_num_threads(1); torch.set_num_interop_threads(1)
 out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
 model,tms=v1.train(a.seed); r=v1.summarize_seed(a.seed,model,tms); raw=r.pop('_raw')
 r['case_id']=f'DIRECT-TTC-V2-{a.seed}'; r['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 (out/'CASE.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
 np.savez_compressed(out/'CASE_EVIDENCE.npz',**raw)
 print(json.dumps({'case_id':r['case_id'],'case':str(out/'CASE.json')},sort_keys=True))
if __name__=='__main__': main()
