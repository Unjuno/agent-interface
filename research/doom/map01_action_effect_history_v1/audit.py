#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from PIL import Image

RUN_SHA='9f9adf50ca1d7e8d553262c9480185d49f9f21b41f55ed7ce09730d5062f1afd'
PREREG_SHA='198a25de2ac8fe7ca06dbf2e177cb703d65219059fc896f627921fe9f0d38e1f'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def desc(path):
    rgb=np.asarray(Image.open(path).convert('RGB'))
    im=Image.fromarray(rgb[10:170,35:285]).convert('L').resize((32,20),Image.Resampling.BILINEAR)
    return np.asarray(im,dtype=np.float32)/255.0, hashlib.sha256(rgb.tobytes()).hexdigest()
def pred(X, cents): return np.array([int(np.argmin([np.mean((row-c)**2) for c in cents])) for row in X])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--prereg',type=Path,required=True);ap.add_argument('--out',type=Path);a=ap.parse_args()
    e=[]; warnings=[]
    if sha(a.source)!=RUN_SHA:e.append('source_sha')
    if sha(a.prereg)!=PREREG_SHA:e.append('prereg_sha')
    s=json.loads((a.root/'summary.json').read_text()); rows=json.loads((a.root/'samples.json').read_text())
    if len(rows)!=320:e.append('sample_count')
    descriptors={}
    for r in rows:
        p=a.root/r['png']
        if not p.exists():e.append('missing:'+r['png']);continue
        d,h=desc(p);descriptors[(r['case'],r['tic'])]=d
        if h!=r['rgb_sha256']:e.append('rgb_hash:'+r['png'])
    train=[r for r in rows if r['case']<12];test=[r for r in rows if r['case']>=12]
    X=np.array([descriptors[(r['case'],r['tic'])].ravel() for r in train]); y=np.array([r['label'] for r in train]); cents=[X[y==z].mean(0) for z in (0,1)]
    TX=np.array([descriptors[(r['case'],r['tic'])].ravel() for r in test]);ty=np.array([r['label'] for r in test]);cur=float((pred(TX,cents)==ty).mean())
    if abs(cur-s['current_only_test_accuracy'])>1e-12:e.append('current_accuracy')
    alias=[]
    for case in range(12,20):
        rs=[r for r in test if r['case']==case];op=[r for r in rs if r['label']==0];cl=[r for r in rs if r['label']==1]
        for o in op:
            od=descriptors[(case,o['tic'])]
            q=min(cl,key=lambda z:float(np.sqrt(np.mean((od-descriptors[(case,z['tic'])])**2))))
            dist=float(np.sqrt(np.mean((od-descriptors[(case,q['tic'])])**2)))
            if dist<=.005: alias.extend([o,q])
    AX=np.array([descriptors[(r['case'],r['tic'])].ravel() for r in alias]);ay=np.array([r['label'] for r in alias]);alias_cur=float((pred(AX,cents)==ay).mean())
    if abs(alias_cur-s['alias_current_accuracy'])>1e-12:e.append('alias_current_accuracy')
    missing_predecessors=[]
    for r in rows:
        prev=(r['case'],r['tic']-1)
        if prev not in descriptors: missing_predecessors.append({'case':r['case'],'tic':r['tic'],'needed_tic':r['tic']-1,'label':r['label']})
    alias_closing=[p for p in s['alias_pairs'] if (p['case'],p['close_tic']-1) not in descriptors]
    history_replayable=len(missing_predecessors)==0;alias_history_replayable=len(alias_closing)==0
    if not alias_history_replayable:warnings.append('critical alias-history evidence cannot be recomputed because closing t165 predecessor t164 PNG was not retained')
    formal=s.get('decision');status='FAIL_AUDIT_INTEGRITY' if e else ('HOLD_EVIDENCE_RETENTION' if not alias_history_replayable else 'PASS_FULL_REPLAY')
    out={'schema':'agent-interface/map01-door-action-effect-history-audit-v1','status':status,'formal_first_outcome':formal,'errors':e,'warnings':warnings,
         'pngs_verified':sum(1 for r in rows if (a.root/r['png']).exists()),'current_classifier_replayed':True,'current_only_test_accuracy':cur,'alias_current_accuracy':alias_cur,
         'history_replayable_from_retained_pngs':history_replayable,'alias_history_replayable_from_retained_pngs':alias_history_replayable,
         'missing_predecessor_count':len(missing_predecessors),'critical_alias_missing_predecessors':alias_closing,
         'disposition':'retain first formal outcome unchanged; do not promote history effect until a separately versioned retention-complete allocation reproduces it'}
    text=json.dumps(out,indent=2)+'\n';print(text,end='')
    if a.out:a.out.write_text(text)
    raise SystemExit(0 if status!='FAIL_AUDIT_INTEGRITY' else 2)
if __name__=='__main__':main()
