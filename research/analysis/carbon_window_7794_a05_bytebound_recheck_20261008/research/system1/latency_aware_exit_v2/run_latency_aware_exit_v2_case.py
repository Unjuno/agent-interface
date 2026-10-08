#!/usr/bin/env python3
import argparse, json, os, sys, resource
from pathlib import Path
import numpy as np
import torch
BASE_DIR=Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR.parent/'latency_aware_exit_v1'))
import run_latency_aware_exit_v1 as v1

ARMS={'ACCURACY_ONLY':v1.LAM_BASE,'LATENCY_AWARE':v1.LAM_FAST}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--mode',choices=['construction','formal-case'],required=True)
    ap.add_argument('--seed',type=int)
    ap.add_argument('--arm',choices=sorted(ARMS))
    ap.add_argument('--out',required=True)
    a=ap.parse_args()
    torch.set_num_threads(1); torch.set_num_interop_threads(1)
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    if a.mode=='construction':
        assert set(v1.FORMAL_SEEDS)=={8891701,8891702,8891703,8891704}
        print(json.dumps({'construction':'PASS_A2_DISPATCH','arms':ARMS,'seeds':v1.FORMAL_SEEDS,'scientific_source':'run_latency_aware_exit_v1.py'},sort_keys=True)); return
    if a.seed not in v1.FORMAL_SEEDS or a.arm not in ARMS: raise SystemExit('invalid frozen case')
    seed=a.seed; arm=a.arm; lam=ARMS[arm]
    xtr,ytr=v1.make_data(seed,v1.TRAIN_N,False)
    xo,yo=v1.make_data(seed+10000,v1.ORD_N,False)
    xs,ys=v1.make_data(seed+20000,v1.STRESS_N,True)
    torch.manual_seed(seed+50000)
    init=v1.EarlyExitNet().state_dict(); init={k:v.clone() for k,v in init.items()}
    model,tms=v1.train_model(seed,lam,init,xtr,ytr)
    r=v1.summarize(seed,arm,lam,model,tms,xo,yo,xs,ys)
    raw=r.pop('_raw')
    raw['yo']=yo; raw['ys']=ys
    r['case_id']=f'A2-{seed}-{arm}'
    r['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    (out/'CASE.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    np.savez_compressed(out/'CASE_EVIDENCE.npz',**raw)
    print(json.dumps({'case_id':r['case_id'],'case':str(out/'CASE.json'),'evidence':str(out/'CASE_EVIDENCE.npz')},sort_keys=True))
if __name__=='__main__': main()
