#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def svg_xy(p):
 root=ET.parse(p).getroot(); ns='{http://www.w3.org/2000/svg}'; d={}
 for r in root.findall('.//'+ns+'rect'):
  if r.attrib.get('id') in ('A','B'): d[r.attrib['id']]=float(r.attrib['x'])
 return d
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--schedule',required=True);p.add_argument('--prereg',required=True);p.add_argument('--src',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 root=Path(a.root); sched=json.load(open(a.schedule)); pre=json.load(open(a.prereg)); src=Path(a.src); errs=[]; rows=[]
 for name,h in pre['source_sha256'].items():
  q=src/name
  if not q.exists() or sha(q)!=h: errs.append(f'source:{name}:{sha(q) if q.exists() else "MISSING"}')
 if len(sched['cases'])!=16: errs.append('schedule_count')
 strata={}
 for exp in sched['cases']:
  cid=exp['case_id']; q=root/cid/'result.json'
  if not q.exists(): errs.append(f'{cid}:missing'); continue
  r=json.load(open(q)); xy=svg_xy(root/cid/'fixture.svg'); dt=r.get('post_anchor_guard_ns'); gc=r['guard']['dark_pixels']; positive=bool(r['guard']['selection_A'])
  timing_ok=isinstance(dt,int) and pre['timing_gate_ns'][0] <= dt <= pre['timing_gate_ns'][1]
  release_ok=bool(r.get('all_relevant_keys_empty')) and bool(r.get('button_empty'))
  ident=(r.get('context')==exp['context'] and r.get('policy')==exp['policy'])
  if not ident: errs.append(f'{cid}:identity')
  if not timing_ok: errs.append(f'{cid}:timing:{dt}')
  if not release_ok: errs.append(f'{cid}:release')
  if not r.get('revalidation',{}).get('success'): errs.append(f'{cid}:revalidation')
  key=f"{exp['context']}|{exp['policy']}"; strata.setdefault(key,[]).append(r)
  rows.append({'id':cid,'context':exp['context'],'policy':exp['policy'],'decision':r['decision'],'guard_positive':positive,'guard_counts':gc,'delta':r['delta'],'post_anchor_guard_ns':dt,'release_ok':release_ok,'A_x':xy['A'],'B_x':xy['B']})
 # stable hard gate
 for pol in ('current_guard_only','history_invalidate'):
  rs=strata.get(f'stable|{pol}',[])
  if len(rs)!=4: errs.append(f'stable:{pol}:n')
  for r in rs:
   if not (r['decision']=='ADMIT' and r['guard']['selection_A'] and abs(r['delta']['A']-10)<1e-9 and abs(r['delta']['B'])<1e-9): errs.append(f'stable:{pol}:outcome')
 cur=strata.get('self_switch|current_guard_only',[]); hist=strata.get('self_switch|history_invalidate',[])
 if len(cur)!=4 or len(hist)!=4: errs.append('switch_n')
 def noinc(rs): return len(rs)==4 and all(r['decision']=='DEPENDENCY_UNAVAILABLE' and not r['guard']['selection_A'] and not r['effect_input_sent'] and abs(r['delta']['A'])<1e-9 and abs(r['delta']['B'])<1e-9 for r in rs)
 def cur_wrong(rs): return len(rs)==4 and all(r['decision']=='ADMIT' and r['guard']['selection_A'] and r['effect_input_sent'] and abs(r['delta']['A'])<1e-9 and abs(r['delta']['B']-10)<1e-9 for r in rs)
 def hist_stop(rs): return len(rs)==4 and all(r['decision']=='STOP_HISTORY_INVALIDATED' and r['guard']['selection_A'] and not r['effect_input_sent'] and abs(r['delta']['A'])<1e-9 and abs(r['delta']['B'])<1e-9 for r in rs)
 if errs: decision='FAIL_INTEGRITY_OR_STABLE_GATE'
 elif noinc(cur) and noinc(hist): decision='NO_INCREMENTAL_HISTORY_AT_TRUE_120MS'
 elif cur_wrong(cur) and hist_stop(hist): decision='PASS_HISTORY_INCREMENT_AT_TRUE_120MS'
 else: decision='HOLD_MIXED_TRUE_120MS'
 out={'schema':'inkscape_action_history_true120_audit_v1','decision':decision,'errors':errs,'rows':rows,'strata_counts':{k:len(v) for k,v in strata.items()},'timing_gate_ns':pre['timing_gate_ns']}
 Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps({'decision':decision,'errors':len(errs)})); raise SystemExit(1 if errs else 0)
if __name__=='__main__': main()
