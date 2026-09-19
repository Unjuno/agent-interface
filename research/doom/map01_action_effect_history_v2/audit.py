#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from PIL import Image

def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def descriptor(rgb):
    im=Image.fromarray(rgb[10:170,35:285]).convert('L').resize((32,20),Image.Resampling.BILINEAR)
    return np.asarray(im,dtype=np.float32)/255.0
def pred(X,cents):return np.array([int(np.argmin([np.mean((row-c)**2) for c in cents])) for row in X])
def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();e=[]
    s=json.loads((a.root/'summary.json').read_text());rows=json.loads((a.root/'samples.json').read_text())
    if len(rows)!=320:e.append('sample_count')
    cur={};delta={}
    for r in rows:
        cp=a.root/r['png'];pp=a.root/r['prev_png']
        if not cp.exists() or not pp.exists():e.append('missing_raw');continue
        c=np.asarray(Image.open(cp).convert('RGB'));q=np.asarray(Image.open(pp).convert('RGB'))
        if sha_bytes(c.tobytes())!=r['rgb_sha256'] or sha_bytes(q.tobytes())!=r['prev_rgb_sha256']:e.append('rgb_hash')
        cd=descriptor(c);pd=descriptor(q);cur[(r['case'],r['tic'])]=cd;delta[(r['case'],r['tic'])]=cd-pd
    train=[r for r in rows if r['case']<12];test=[r for r in rows if r['case']>=12]
    Xc=np.array([cur[(r['case'],r['tic'])].ravel() for r in train]);Xd=np.array([delta[(r['case'],r['tic'])].ravel() for r in train]);y=np.array([r['label'] for r in train])
    cc=[Xc[y==z].mean(0) for z in (0,1)];dc=[Xd[y==z].mean(0) for z in (0,1)]
    Tc=np.array([cur[(r['case'],r['tic'])].ravel() for r in test]);Td=np.array([delta[(r['case'],r['tic'])].ravel() for r in test]);ty=np.array([r['label'] for r in test])
    ca=float((pred(Tc,cc)==ty).mean());da=float((pred(Td,dc)==ty).mean())
    alias=[];pairs=[]
    for case in range(12,20):
        rs=[r for r in test if r['case']==case];op=[r for r in rs if r['label']==0];cl=[r for r in rs if r['label']==1]
        for o in op:
            od=cur[(case,o['tic'])];q=min(cl,key=lambda z:float(np.sqrt(np.mean((od-cur[(case,z['tic'])])**2))))
            d=float(np.sqrt(np.mean((od-cur[(case,q['tic'])])**2)))
            if d<=.005:pairs.append((case,o['tic'],q['tic']));alias.extend([o,q])
    Ac=np.array([cur[(r['case'],r['tic'])].ravel() for r in alias]);Ad=np.array([delta[(r['case'],r['tic'])].ravel() for r in alias]);ay=np.array([r['label'] for r in alias])
    aca=float((pred(Ac,cc)==ay).mean()) if len(alias) else None;ada=float((pred(Ad,dc)==ay).mean()) if len(alias) else None
    expected={'current_only_test_accuracy':ca,'delta_history_test_accuracy':da,'alias_current_accuracy':aca,'alias_history_accuracy':ada}
    for k,v in expected.items():
        if v is None or abs(v-s[k])>1e-12:e.append(k)
    if len(pairs)!=len(s['alias_pairs']):e.append('alias_pair_count')
    gates={'alias_pairs_at_least_6':len(pairs)>=6,'alias_current_accuracy_le_0_75':aca is not None and aca<=.75,'alias_history_accuracy_ge_0_95':ada is not None and ada>=.95,'full_raw_replay':not e}
    scientific='SUPPORT_ACTION_EFFECT_HISTORY' if gates['alias_pairs_at_least_6'] and gates['alias_current_accuracy_le_0_75'] and gates['alias_history_accuracy_ge_0_95'] else 'FAIL_ACTION_EFFECT_HISTORY_HYPOTHESIS'
    status='PASS_FULL_REPLAY' if not e and scientific==s['decision'] else 'FAIL_AUDIT'
    out={'schema':'agent-interface/map01-door-action-effect-history-audit-v2','status':status,'scientific_decision':scientific,'formal_decision':s['decision'],'errors':e,'raw_pngs_verified':len(rows)*2,'alias_pairs':len(pairs),**expected,'gates':gates}
    text=json.dumps(out,indent=2)+'\n';print(text,end='');
    if a.out:a.out.write_text(text)
    raise SystemExit(0 if status=='PASS_FULL_REPLAY' else 2)
if __name__=='__main__':main()
