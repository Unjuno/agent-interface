from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
EXPECTED='3d3133ea34205324545de76b99d9f65e450d45451a705443336f71a5ac6a7ffd'
def hbytes(b): return hashlib.sha256(b).hexdigest()
def fp(v): return hashlib.sha256(json.dumps(v,separators=(',',':')).encode()).hexdigest()
def check(root:Path):
 rows=json.loads((root/'results.json').read_text()); errors=[]
 if len(rows)!=3: errors.append('case_count')
 for i,r in enumerate(rows):
  c=root/f'case-{i:02d}'
  rep=json.loads((c/'report.json').read_text())
  if rep!= {k:v for k,v in r.items() if k not in ('case','process_returncode')}: errors.append(f'{i}:result_report_mismatch')
  base=(c/'baseline.server.xkb').read_bytes(); after=(c/'after.server.xkb').read_bytes(); de=(c/'de.resolved.xkb').read_bytes()
  if hbytes(base)!=r['baseline_server_sha256']: errors.append(f'{i}:baseline_hash')
  if hbytes(after)!=r['after_server_sha256']: errors.append(f'{i}:after_hash')
  if hbytes(de)!=r['de_resolved_sha256'] or hbytes(de)!=EXPECTED: errors.append(f'{i}:de_hash')
  if after!=de: errors.append(f'{i}:after_not_exact_de')
  if fp(r['baseline_map'])!=r['core_map_before_sha256']: errors.append(f'{i}:before_map_hash')
  if fp(r['after_map'])!=r['core_map_after_sha256']: errors.append(f'{i}:after_map_hash')
  if fp(r['baseline_modifiers'])!=r['modifier_before_sha256']: errors.append(f'{i}:before_mod_hash')
  if fp(r['after_modifiers'])!=r['modifier_after_sha256']: errors.append(f'{i}:after_mod_hash')
  if (base!=after)!=r['server_changed']: errors.append(f'{i}:server_changed')
  if (r['baseline_map']!=r['after_map'])!=r['core_map_changed']: errors.append(f'{i}:map_changed')
  if (r['baseline_modifiers']!=r['after_modifiers'])!=r['modifier_changed']: errors.append(f'{i}:mod_changed')
 out={'status':'PASS_STRICT_POSTHOC' if not errors else 'FAIL_STRICT_POSTHOC','errors':errors,'cases':len(rows)}
 print(json.dumps(out,indent=2)); return out
if __name__=='__main__': raise SystemExit(0 if check(Path(sys.argv[1]))['status'].startswith('PASS') else 1)
