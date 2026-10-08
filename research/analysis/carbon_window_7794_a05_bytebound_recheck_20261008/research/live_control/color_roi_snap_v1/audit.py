#!/usr/bin/env python3
import argparse, base64, hashlib, json
from collections import deque, Counter
from pathlib import Path
NEUTRAL=[30,30]
POS={'UNIQUE_X','UNIQUE_DIAG','UNIQUE_NEG'}
NEG={'DUPLICATE','ABSENT','OUTSIDE_ROI'}

def inside(pt,rect): return bool(rect and rect[0]<=pt[0]<rect[2] and rect[1]<=pt[1]<rect[3])
def comps(raw,w,h,pix):
 m=set()
 for y in range(h):
  for x in range(w):
   i=(y*w+x)*4
   if raw[i:i+4]==pix:m.add((x,y))
 out=[]
 while m:
  s=m.pop(); q=deque([s]); pts=[s]
  while q:
   x,y=q.popleft()
   for n in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
    if n in m:m.remove(n);q.append(n);pts.append(n)
  xs=[p[0] for p in pts];ys=[p[1] for p in pts]
  out.append((len(pts),[min(xs),min(ys),max(xs)+1,max(ys)+1]))
 return sorted(out,key=lambda z:(z[1][1],z[1][0]))

def audit_data(data,base,reps):
 rows=data['rows']; errs=[]; checks=0
 expected_n=12*reps
 if len(rows)!=expected_n: errs.append(f'case_count:{len(rows)}')
 ids=[r['case_id'] for r in rows]
 if len(ids)!=len(set(ids)):errs.append('duplicate_case_id')
 expected=Counter((s,p) for _ in range(reps) for s in sorted(POS|NEG) for p in ['DIRECT','ROI_SNAP'])
 got=Counter((r['scenario'],r['policy']) for r in rows)
 if got!=expected:errs.append('matrix_mismatch')
 snap_pos=direct_pos=snap_refuse=snap_decoy=0
 for r in rows:
  checks+=1; c=r['candidate']; truth=r['truth']; pol=r['policy']; sc=r['scenario']
  if c['before']!=NEUTRAL:errs.append(r['case_id']+':before')
  if c['mask_before']!=0 or c['mask_after']!=0:errs.append(r['case_id']+':mask')
  if r['candidate_exit']!=0 or r['candidate_stderr']!='':errs.append(r['case_id']+':candidate_process')
  if r['score']['target_hit']!=inside(c['after'],truth['target_rect']):errs.append(r['case_id']+':score_target')
  if r['score']['decoy_hit']!=any(inside(c['after'],x) for x in truth['decoy_rects']):errs.append(r['case_id']+':score_decoy')
  if pol=='DIRECT':
   if c['after']!=truth['coarse'] or not c['motion_emitted']:errs.append(r['case_id']+':direct_motion')
   if sc in POS and not r['score']['target_hit']: direct_pos+=1
  else:
   roi=c.get('roi')
   if not roi:errs.append(r['case_id']+':roi_missing');continue
   try: raw=base64.b64decode(roi['base64'],validate=True)
   except Exception: errs.append(r['case_id']+':roi_base64'); continue
   if len(raw)!=roi['w']*roi['h']*4 or hashlib.sha256(raw).hexdigest()!=roi['sha256']:errs.append(r['case_id']+':roi_bytes')
   cc=comps(raw,roi['w'],roi['h'],bytes.fromhex(c['target_pixel_hex'])); adm=[x for x in cc if 400<=x[0]<=700 and (x[1][2]-x[1][0])<=26 and (x[1][3]-x[1][1])<=26]
   if len(adm)!=len(c['admissible_components']):errs.append(r['case_id']+':component_count')
   if sc in POS:
    if not (c['decision']=='SNAP' and c['motion_emitted'] and r['score']['target_hit'] and not r['score']['decoy_hit']):errs.append(r['case_id']+':snap_positive')
    else:snap_pos+=1
   else:
    if c['motion_emitted'] or c['after']!=NEUTRAL or not c['decision'].startswith('YIELD_'):errs.append(r['case_id']+':snap_refusal')
    else:snap_refuse+=1
   if r['score']['decoy_hit']:snap_decoy+=1
 for r in rows:
  try: pr=json.loads((base/r['case_id']/'processes.json').read_text()); checks+=1
  except Exception: errs.append(r['case_id']+':process_receipt_missing'); continue
  if pr['fixture_exit'] != 0 or pr['xvfb_exit'] not in (0,-15) or not pr['socket_absent']:errs.append(r['case_id']+':cleanup')
 gates=(snap_pos==3*reps and direct_pos==3*reps and snap_refuse==3*reps and snap_decoy==0)
 disp=('PASS_COLOR_ROI_SNAP_BOUNDARY_SCOPED' if reps==3 else 'PASS_CONSTRUCTION_SCOPED') if not errs and gates else 'FAIL_OR_HOLD'
 return {'schema':'color-roi-snap-audit-v1','checks':checks,'errors':errs,'snap_positive_pass':snap_pos,'direct_positive_misses':direct_pos,'snap_refusals':snap_refuse,'snap_decoy_hits':snap_decoy,'reps':reps,'disposition':disp}

def main():
 p=argparse.ArgumentParser();p.add_argument('raw');p.add_argument('--reps',type=int,default=3);a=p.parse_args(); rp=Path(a.raw); result=audit_data(json.loads(rp.read_text()),rp.parent,a.reps)
 print(json.dumps(result,sort_keys=True,indent=2)); return 0 if not result['errors'] and result['disposition'].startswith('PASS_') else 1
if __name__=='__main__': raise SystemExit(main())
