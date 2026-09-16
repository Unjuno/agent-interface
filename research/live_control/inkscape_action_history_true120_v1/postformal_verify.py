#!/usr/bin/env python3
import argparse,json,hashlib
from pathlib import Path
from PIL import Image
import xml.etree.ElementTree as ET

def guard_counts(p):
 im=Image.open(p).convert('RGB'); w,h=im.size; obj_w,obj_h=158,105
 def dark(x0,y0,x1,y1): return sum(1 for y in range(max(0,y0),min(h,y1)) for x in range(max(0,x0),min(w,x1)) if max(im.getpixel((x,y)))<=60)
 return {'top':dark(0,0,obj_w,20),'right':dark(obj_w,0,obj_w+20,obj_h+40),'bottom':dark(0,obj_h+20,obj_w,obj_h+40)},hashlib.sha256(im.tobytes()).hexdigest()
def xy(p):
 root=ET.parse(p).getroot();ns='{http://www.w3.org/2000/svg}';d={}
 for r in root.findall('.//'+ns+'rect'):
  if r.attrib.get('id') in ('A','B'): d[r.attrib['id']]=float(r.attrib['x'])
 return d
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--schedule',required=True);a=ap.parse_args();root=Path(a.root);sched=json.load(open(a.schedule));errs=[];rows=[]
 for exp in sched['cases']:
  cid=exp['case_id'];d=root/cid;r=json.load(open(d/'result.json')); counts,rgb=guard_counts(d/'guard_roi.png'); pos=(counts['top']>=30 and counts['right']>=80 and counts['bottom']>=30); pos_claim=bool(r['guard']['selection_A']); dt=r['timestamps']['guard_start_ns']-r['timestamps']['guard_anchor_ns']
  if counts!=r['guard']['dark_pixels']:errs.append(f'{cid}:guard_counts')
  if rgb!=r['guard']['rgb_sha256']:errs.append(f'{cid}:guard_rgb')
  if pos!=pos_claim:errs.append(f'{cid}:guard_positive')
  if dt!=r['post_anchor_guard_ns'] or not (120_000_000<=dt<=150_000_000):errs.append(f'{cid}:timing')
  if exp['context']=='self_switch':
   q=r['action_receipts']
   if len(q)!=1 or q[0]['kind']!='selection_navigation' or q[0]['key']!='Tab':errs.append(f'{cid}:receipt')
   else:
    if r['timestamps']['guard_anchor_ns']!=q[0]['end_ns']:errs.append(f'{cid}:anchor')
    if not (r['timestamps']['revalidation_complete_ns'] < q[0]['start_ns'] <= q[0]['end_ns'] < r['timestamps']['guard_start_ns']):errs.append(f'{cid}:order')
  else:
   if r['action_receipts'] or r['timestamps']['guard_anchor_ns']!=r['timestamps']['revalidation_complete_ns']:errs.append(f'{cid}:stable_anchor')
  final=xy(d/'fixture.svg'); da=final['A']-r['initial_svg']['A']['x'];db=final['B']-r['initial_svg']['B']['x']
  if abs(da-r['delta']['A'])>1e-9 or abs(db-r['delta']['B'])>1e-9:errs.append(f'{cid}:svg_delta')
  if not r['all_relevant_keys_empty'] or not r['button_empty']:errs.append(f'{cid}:release')
  rows.append({'id':cid,'guard_counts':counts,'guard_rgb_sha256':rgb,'post_anchor_guard_ns':dt,'decision':r['decision'],'delta':r['delta']})
 out={'schema':'inkscape_action_history_true120_postformal_verify_v1','status':'PASS' if not errs else 'FAIL','errors':errs,'rows':rows}; print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if not errs else 1)
if __name__=='__main__':main()
