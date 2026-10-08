#!/usr/bin/env python3
import argparse,json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
NS='{http://www.w3.org/2000/svg}'
ZERO='00'*32

def sh(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pos(p):
 r=ET.parse(p).getroot();d={}
 for e in r.findall(NS+'rect'):
  if e.attrib.get('id') in ('A','B'):d[e.attrib['id']]=float(e.attrib['x'])
 return d
ap=argparse.ArgumentParser();ap.add_argument('root');ap.add_argument('prereg');a=ap.parse_args();root=Path(a.root);pre=json.loads(Path(a.prereg).read_text())
errors=[]; stats={k:0 for k in ['snapshot_ready','snapshot_fail','wait_ready','wait_fail','snapshot_stable_correct','snapshot_switch_wrong','wait_stable_correct','wait_switch_wrong','fail_closed']}
for row in pre['schedule']:
 p=root/row['case_id']/'result.json'
 if not p.exists():errors.append('missing:'+row['case_id']);continue
 r=json.loads(p.read_text())
 if r.get('case_id')!=row['case_id'] or r.get('trajectory')!=row['trajectory'] or r.get('readiness')!=row['readiness']: errors.append('identity:'+row['case_id']);continue
 rr=r.get('readiness_result'); ready=bool(rr and rr.get('ready'))
 pref=row['readiness']
 stats[pref+'_ready' if ready else pref+'_fail']+=1
 if not ready:
  if 'effect_start_ns' in r or 'saved_svg_sha256' in r:errors.append('failed_not_closed:'+row['case_id'])
  else:stats['fail_closed']+=1
  continue
 sv=root/row['case_id']/'saved.svg'
 if not sv.exists():errors.append('saved_missing:'+row['case_id']);continue
 if r.get('saved_svg_sha256')!=sh(sv):errors.append('saved_hash:'+row['case_id'])
 d=pos(sv); traj=row['trajectory']
 if r.get('keymap_after_effect_hex')!=ZERO or r.get('keymap_after_save_hex')!=ZERO:errors.append('keymap:'+row['case_id'])
 if traj=='stable':
  ok=abs(d.get('A',-99)-60)<.5 and abs(d.get('B',-99)-220)<.5
  if ok:stats[pref+'_stable_correct']+=1
  else:errors.append('stable_effect:'+row['case_id']+':'+repr(d))
 else:
  ok=abs(d.get('A',-99)-50)<.5 and abs(d.get('B',-99)-230)<.5
  if ok:stats[pref+'_switch_wrong']+=1
  else:errors.append('switch_effect:'+row['case_id']+':'+repr(d))
hard_safety=not errors
if hard_safety and stats['wait_ready']==20 and stats['snapshot_fail']>=1:
 decision='PROMOTE_BOUNDED_READINESS_WAIT_SCOPED'
elif hard_safety:
 decision='HOLD'
else:decision='FAIL'
out={'schema':'inkscape-selection-readiness-audit-v1','task':pre['task'],'stats':stats,'errors':errors,'hard_safety_pass':hard_safety,'decision':decision}
print(json.dumps(out,sort_keys=True,indent=2)); raise SystemExit(0 if hard_safety else 1)
