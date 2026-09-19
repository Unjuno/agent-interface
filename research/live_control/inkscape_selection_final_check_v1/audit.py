#!/usr/bin/env python3
import argparse,hashlib,json,math
from pathlib import Path
from PIL import Image
from xml.etree import ElementTree as ET
DARK=60; MINC=100; TOL=.001

def sha(p):
 h=hashlib.sha256(); h.update(Path(p).read_bytes()); return h.hexdigest()
def handles(im,box):
 x0,y0,x1,y1=box
 strips={'top':(max(0,x0-22),max(0,y0-22),min(im.width,x1+22),y0),'bottom':(max(0,x0-22),y1,min(im.width,x1+22),min(im.height,y1+25)),'left':(max(0,x0-27),max(0,y0-17),x0,min(im.height,y1+17)),'right':(x1,max(0,y0-17),min(im.width,x1+29),min(im.height,y1+17))}
 return {n:sum(1 for r,g,b in im.crop(reg).getdata() if r<DARK and g<DARK and b<DARK) for n,reg in strips.items()}
def selected(c): return all(v>=MINC for v in c.values())
def parse_svg(p):
 root=ET.parse(p).getroot(); out={}
 for e in root.iter():
  if e.attrib.get('id') in ('A','B'):
   k=e.attrib['id']; out[k]={q:float(e.attrib[q]) for q in ('x','y','width','height')}; out[k]['fill']=e.attrib.get('fill','')
 return out
def eq(a,b): return abs(a-b)<=TOL

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('root'); a=ap.parse_args(); root=Path(a.root)
 sched=json.loads((root/'schedule.json').read_text())['ordered_scenarios']; rows=[json.loads(x) for x in (root/'ledger.jsonl').read_text().splitlines() if x.strip()]
 errs=[]; agg={s:0 for s in ['stable','switch_to_B','A_B_A','unrelated_pointer']}
 if len(rows)!=20: errs.append(f'rows={len(rows)}')
 if [r['scenario'] for r in rows]!=sched: errs.append('schedule_mismatch')
 for r in rows:
  cid=r['case_id']; s=r['scenario']; agg[s]+=1
  if r['returncode']!=0 or 'result' not in r: errs.append(cid+':process'); continue
  d=root/cid; z=r['result']; im=Image.open(d/'final_check.png').convert('RGB')
  ac=handles(im,z['red_bbox']); bc=handles(im,z['blue_bbox']); a_sel=selected(ac); b_sel=selected(bc)
  geom=parse_svg(d/'case.svg'); dxA=geom['A']['x']-50.; dxB=geom['B']['x']-190.
  if sha(d/'final_check.png')!=z['image_sha256']['final_check.png']: errs.append(cid+':image_hash')
  if not z['initial_check'] or not z['focus_same']: errs.append(cid+':initial_or_focus')
  for phase in ['pre_physical','post_physical','final_physical']:
   if z[phase]['pressed_keycodes'] or z[phase]['buttons']: errs.append(cid+':physical_'+phase)
  if not (eq(geom['A']['y'],70) and eq(geom['B']['y'],70) and eq(geom['A']['width'],60) and eq(geom['B']['width'],60) and eq(geom['A']['height'],40) and eq(geom['B']['height'],40)): errs.append(cid+':other_geometry')
  if s=='switch_to_B':
   if a_sel or not b_sel or z['effect_started'] or not eq(dxA,0) or not eq(dxB,0): errs.append(cid+f':switch_gate a={ac} b={bc} effect={z["effect_started"]} dx={dxA},{dxB}')
  else:
   if not a_sel or b_sel or not z['effect_started'] or not eq(dxA,2) or not eq(dxB,0): errs.append(cid+f':valid_gate a={ac} b={bc} effect={z["effect_started"]} dx={dxA},{dxB}')
  names=[e['event'] for e in z['events']]
  if 'final_check' not in names or (('effect_admit' if z['effect_started'] else 'effect_refuse') not in names): errs.append(cid+':events')
  else:
   if names.index('final_check')>names.index('effect_admit' if z['effect_started'] else 'effect_refuse'): errs.append(cid+':order')
 if any(v!=5 for v in agg.values()): errs.append('strata='+repr(agg))
 out={'audit':'PASS_SELECTION_FINAL_CHECK_AUDIT' if not errs else 'FAIL_SELECTION_FINAL_CHECK_AUDIT','cases':len(rows),'strata':agg,'errors':errs}
 (root/'audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)); print(json.dumps(out,indent=2,sort_keys=True)); return 0 if not errs else 1
if __name__=='__main__': raise SystemExit(main())
