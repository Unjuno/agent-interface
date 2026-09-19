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
        aa=np.asarray(ia.convert('RGB'),dtype=np.float32);bb=np.asarray(ib.convert('RGB'),dtype=np.float32)
    return float(np.abs(aa-bb).mean()/255.0)
def audit_case(d):
    r=json.loads((d/'result.json').read_text()); errs=[]
    if r['validity_status']!='VALID_CURRENT': errs.append('validity_not_current')
    if r['source_health']!=97 or r['post_health']!=97 or r['source_ammo']!=48 or r['post_ammo']!=48: errs.append('signal_drift')
    if not r['release'] or r['release'].get('verified') is not True or r['release'].get('keys_down')!=[] or r['release'].get('buttons_down')!=[]: errs.append('release')
    if r['terminal_status']!='completed': errs.append('terminal')
    if r['score']!={'kill_count':0,'death_count':0,'map_exit':False,'player_dead':False}: errs.append('score')
    if rgb_sha(r['source_image'])!=r['source_frame_rgb_sha256'] or rgb_sha(r['post_image'])!=r['post_frame_rgb_sha256']: errs.append('frame_hash')
    m=mae(r['source_image'],r['post_image'])
    if abs(m-r['viewport_normalized_mae'])>1e-9: errs.append('mae')
    if (m>THRESHOLD)!=r['visible_change']: errs.append('visible_class')
    return {'id':r['id'],'pair':r['pair'],'arm':r['arm'],'pass':not errs,'errors':errs,'mae':m,'validity':r['validity_status'],'visible_change':m>THRESHOLD}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--evidence',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    rows=[audit_case(p) for p in sorted(a.evidence.iterdir()) if p.is_dir() and (p/'result.json').exists()]
    by={}
    for r in rows:by.setdefault(r['pair'],{})[r['arm']]=r
    pairs=[]
    for pair,arms in sorted(by.items()):
        c=arms['coast'];rec=arms['recovery'];pairs.append({'pair':pair,'coast_mae':c['mae'],'recovery_mae':rec['mae'],'ratio':rec['mae']/max(c['mae'],1e-12),'both_valid':c['validity']=='VALID_CURRENT' and rec['validity']=='VALID_CURRENT','recovery_visible':rec['visible_change'],'recovery_gt_coast':rec['mae']>c['mae']})
    decision='PASS_BLINDSPOT_SCOPED' if len(rows)==6 and all(r['pass'] for r in rows) and all(p['both_valid'] and p['recovery_visible'] and p['recovery_gt_coast'] for p in pairs) else 'HOLD_OR_FAIL'
    out={'schema':'recovery-admission-blindspot-audit-v1','cases':rows,'pairs':pairs,'decision':decision,'pass':decision=='PASS_BLINDSPOT_SCOPED'}
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
