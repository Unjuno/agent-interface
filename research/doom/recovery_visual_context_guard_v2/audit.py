from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from PIL import Image
THRESHOLD=.015

def rgb_sha(p):
    with Image.open(p) as im: return hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()
def mae(a,b):
    with Image.open(a) as ia, Image.open(b) as ib:
        aa=np.asarray(ia.convert('RGB'),dtype=np.float32); bb=np.asarray(ib.convert('RGB'),dtype=np.float32)
    return float(np.abs(aa-bb).mean()/255.0)
def verdict(m): return 'ADMIT' if m <= THRESHOLD else 'REJECT_CONTEXT_CHANGED'
def audit_case(d):
    r=json.loads((d/'result.json').read_text()); errs=[]
    if r['baseline_validity_status']!='VALID_CURRENT': errs.append('baseline_not_current')
    if r['source_health']!=97 or r['post_health']!=97 or r['source_ammo']!=48 or r['post_ammo']!=48: errs.append('signal_drift')
    if not r['release'] or r['release'].get('verified') is not True or r['release'].get('keys_down')!=[] or r['release'].get('buttons_down')!=[]: errs.append('release')
    if r['terminal_status']!='completed': errs.append('terminal')
    if r['score']!={'kill_count':0,'death_count':0,'map_exit':False,'player_dead':False}: errs.append('score')
    if rgb_sha(r['source_image'])!=r['source_frame_rgb_sha256'] or rgb_sha(r['post_image'])!=r['post_frame_rgb_sha256']: errs.append('frame_hash')
    m=mae(r['source_image'],r['post_image'])
    if abs(m-r['viewport_normalized_mae'])>1e-9: errs.append('mae')
    if r['visual_context_threshold']!=THRESHOLD: errs.append('threshold')
    if r['visual_context_verdict']!=verdict(m): errs.append('guard_verdict')
    expected='ADMIT' if r['arm']=='coast' else 'REJECT_CONTEXT_CHANGED'
    if r['visual_context_verdict']!=expected: errs.append('arm_expected_guard')
    return {'id':r['id'],'pair':r['pair'],'arm':r['arm'],'pass':not errs,'errors':errs,'mae':m,'baseline':r['baseline_validity_status'],'guard':r['visual_context_verdict']}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--evidence',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    rows=[audit_case(p) for p in sorted(a.evidence.iterdir()) if p.is_dir() and (p/'result.json').exists()]
    by={}
    for r in rows:by.setdefault(r['pair'],{})[r['arm']]=r
    pairs=[]
    for pair,arms in sorted(by.items()):
        c=arms['coast']; rec=arms['recovery']; pairs.append({'pair':pair,'coast_mae':c['mae'],'recovery_mae':rec['mae'],'both_baseline_valid':c['baseline']=='VALID_CURRENT' and rec['baseline']=='VALID_CURRENT','coast_admit':c['guard']=='ADMIT','recovery_reject':rec['guard']=='REJECT_CONTEXT_CHANGED'})
    ok=len(rows)==8 and all(r['pass'] for r in rows) and len(pairs)==4 and all(p['both_baseline_valid'] and p['coast_admit'] and p['recovery_reject'] for p in pairs)
    decision='PASS_VISUAL_CONTEXT_GUARD_SCOPED' if ok else 'HOLD_VISUAL_CONTEXT_GUARD'
    out={'schema':'recovery-visual-context-guard-audit-v1','cases':rows,'pairs':pairs,'decision':decision,'pass':ok}
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
