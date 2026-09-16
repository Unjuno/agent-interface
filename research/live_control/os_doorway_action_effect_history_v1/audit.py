#!/usr/bin/env python3
import argparse, hashlib, json, math
from pathlib import Path
from PIL import Image

def sha_rgb(path):
    im=Image.open(path).convert('RGB'); return hashlib.sha256(im.tobytes()).hexdigest(),im

def centroid(im):
    pix=im.load(); xs=[]
    for y in range(40,160):
        for x in range(70,250):
            r,g,b=pix[x,y]
            if 35<=r<=80 and 35<=g<=80 and 35<=b<=80: xs.append(x)
    if not xs: raise ValueError('panel absent')
    return sum(xs)/len(xs)

p=argparse.ArgumentParser(); p.add_argument('--schedule',required=True); p.add_argument('--results',required=True); p.add_argument('--out',required=True); p.add_argument('--prereg',required=True); p.add_argument('--src-root',required=True); a=p.parse_args()
s=json.load(open(a.schedule)); pre=json.load(open(a.prereg)); root=Path(a.results); src=Path(a.src_root); errors=[]; rows=[]
for name,expected_sha in pre['source_sha256'].items():
    try: actual=hashlib.sha256((src/name).read_bytes()).hexdigest()
    except Exception as e: errors.append(f'source_read:{name}:{type(e).__name__}') ; continue
    if actual!=expected_sha: errors.append(f'source_hash:{name}:{actual}')
if len(s['cases'])!=24: errors.append('schedule_count')
by_policy={'current_only':[], 'history':[]}; current_hashes=set()
for exp in s['cases']:
    cid=exp['case_id']; d=root/cid
    try:
        r=json.load(open(d/'result.json'))
        psha,pim=sha_rgb(d/'predecessor.png'); csha,cim=sha_rgb(d/'current.png'); fsha,fim=sha_rgb(d/'final.png')
        pc,cc=centroid(pim),centroid(cim); current_hashes.add(csha)
        expected='Right' if exp['trajectory']=='opening' else 'Left'
        if r['case_id']!=cid or r['policy']!=exp['policy'] or r['trajectory']!=exp['trajectory']: errors.append(f'{cid}:identity')
        if r['predecessor_rgb_sha256']!=psha or r['current_rgb_sha256']!=csha or r['final_rgb_sha256']!=fsha: errors.append(f'{cid}:image_hash')
        if abs(cc-159.5)>0.6: errors.append(f'{cid}:current_centroid:{cc}')
        if exp['trajectory']=='opening' and not pc<cc: errors.append(f'{cid}:history_sign_open')
        if exp['trajectory']=='closing' and not pc>cc: errors.append(f'{cid}:history_sign_close')
        if exp['policy']=='history' and r['decision']!=expected: errors.append(f'{cid}:history_decision')
        if exp['policy']=='current_only' and r['decision']!='Right': errors.append(f'{cid}:baseline_decision')
        if r['effect']['observed_action']!=r['decision']: errors.append(f'{cid}:effect_action')
        truth=(r['decision']==expected)
        if bool(r['task_correct'])!=truth or bool(r['effect']['correct'])!=truth: errors.append(f'{cid}:truth')
        if r['pre_key_down'] or r['post_key_down'] or not r['input_empty']: errors.append(f'{cid}:release')
        by_policy[exp['policy']].append(truth)
        rows.append({'case_id':cid,'policy':exp['policy'],'trajectory':exp['trajectory'],'expected':expected,'decision':r['decision'],'correct':truth,'pred_centroid':pc,'current_centroid':cc,'current_sha256':csha})
    except Exception as e:
        errors.append(f'{cid}:exception:{type(e).__name__}:{e}')
for pol in by_policy:
    traj=[x['trajectory'] for x in s['cases'] if x['policy']==pol]
    if traj.count('opening')!=6 or traj.count('closing')!=6: errors.append(f'{pol}:balance')
h=sum(by_policy['history']); b=sum(by_policy['current_only'])
if len(current_hashes)!=1: errors.append(f'current_not_identical:{len(current_hashes)}')
if h!=12: errors.append(f'history_correct:{h}')
if b!=6: errors.append(f'baseline_correct:{b}')
decision='PASS_OS_DOORWAY_HISTORY_SCOPED' if not errors else 'FAIL_INTEGRITY_OR_GATE'
out={'decision':decision,'errors':errors,'history_correct':h,'history_total':12,'current_only_correct':b,'current_only_total':12,'unique_current_rgb_hashes':sorted(current_hashes),'rows':rows}
Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps({k:out[k] for k in ['decision','errors','history_correct','current_only_correct','unique_current_rgb_hashes']},sort_keys=True))
raise SystemExit(0 if not errors else 1)
