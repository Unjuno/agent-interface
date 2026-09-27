#!/usr/bin/env python3
import json,hashlib,sys
from pathlib import Path
root=Path(sys.argv[1]);s=json.loads((root/'SUMMARY.json').read_text());errs=[]
if s['allocation']!='c284-flock-01' or s['order']!=['stable','stale_restoremtime'] or len(s['rows'])!=2:errs.append('summary shape')
for r in s['rows']:
 if not r.get('lock',{}).get('acquired'):errs.append(r['arm']+':lock')
 if not r.get('release',{}).get('verified') or r['release'].get('keys_down') or r['release'].get('buttons_down'):errs.append(r['arm']+':release')
 if r.get('scorer_exitcode')!=0 or not r.get('score',{}).get('xlsx_read_ok'):errs.append(r['arm']+':score')
 if r['arm']=='stable' and r['classification']!='stable_saved':errs.append('stable not saved')
 if r['arm']=='stale_restoremtime':
  a=r.get('after_external_restoremtime',{}).get('file',{});p=r['precheck']['file']
  if a.get('ino')!=p.get('ino') or a.get('mtime_ns')!=p.get('mtime_ns') or a.get('sha256')==p.get('sha256'):errs.append('mutation invariant')
def gitblob(p):
 b=p.read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
if gitblob(root.parent.parent/'backend_x11.py')!='b4f8e043ce4f8929d446e038418ea0fd3655bab0':errs.append('backend blob')
if gitblob(root.parent.parent/'office_backend.py')!='3aeca10f62fb1366bcdd5fad561509cfcc0d91ab':errs.append('office blob')
print(json.dumps({'pass':not errs,'errors':errs,'stale_class':s['rows'][1]['classification']},indent=2));sys.exit(bool(errs))
