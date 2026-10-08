#!/usr/bin/env python3
import argparse,json,pathlib,tempfile
import audit

def load(root):
 root=pathlib.Path(root); rows=[]; errors=[]
 for rep in range(3):
  b=root/f'batch-{rep}'
  if not (b/'ROWS.json').exists(): errors.append(f'missing_rows:{rep}'); continue
  rs=json.loads((b/'ROWS.json').read_text())
  if len(rs)!=12: errors.append(f'batch_count:{rep}:{len(rs)}')
  if any(type(r.get('rep')) is not int or r.get('rep')!=rep for r in rs): errors.append(f'batch_rep:{rep}')
  if not (b/'END.json').exists(): errors.append(f'missing_end:{rep}')
  else:
   end=json.loads((b/'END.json').read_text())
   if end.get('rep')!=rep or end.get('rows')!=12 or end.get('exit')!=0: errors.append(f'end:{rep}')
  ext=root/f'batch-{rep}.external_exit.txt'
  if not ext.exists() or ext.read_text().strip()!='0': errors.append(f'external_exit:{rep}')
  rows.extend(rs)
 return rows,errors

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--out',required=True); a=ap.parse_args(); rows,errors=load(a.root)
 with tempfile.TemporaryDirectory() as d:
  p=pathlib.Path(d); (p/'ROWS.json').write_text(json.dumps(rows)); base=audit.audit(p,3)
 errors.extend(base['errors'])
 result={'decision':'PASS_EFFECT_OWNER_DEADLINE_SCOPED' if not errors else 'FAIL_OR_HOLD','rows':len(rows),'errors':errors,'batch_exits':[0,0,0] if not any(e.startswith('external_exit') for e in errors) else None}
 pathlib.Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,sort_keys=True)); raise SystemExit(0 if not errors else 1)
if __name__=='__main__': main()
