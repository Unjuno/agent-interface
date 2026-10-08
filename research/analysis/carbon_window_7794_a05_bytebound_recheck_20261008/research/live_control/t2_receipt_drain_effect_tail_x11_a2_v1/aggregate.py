#!/usr/bin/env python3
import argparse, json, hashlib, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from experiment import summarize, FRONTIER_MS, HOLD_MS
p=argparse.ArgumentParser(); p.add_argument('--batches',nargs=4,required=True); p.add_argument('--out',required=True); a=p.parse_args()
rows=[]; batch_hashes=[]
for i,f in enumerate(a.batches):
    path=Path(f); raw=path.read_bytes(); batch_hashes.append(hashlib.sha256(raw).hexdigest()); r=json.loads(raw)
    ids=[x['case_id'] for x in r['rows']]
    expected=list(range(i*8,i*8+8))
    if ids!=expected: raise SystemExit(f'batch{i} ids {ids} != {expected}')
    rows.extend(r['rows'])
ids=[x['case_id'] for x in rows]
if ids!=list(range(32)): raise SystemExit('global ids mismatch')
out={'schema':2,'frontier_ms':FRONTIER_MS,'hold_ms':HOLD_MS,'batch_sha256':batch_hashes,'rows':rows,'summary':summarize(rows)}
Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True),encoding='utf-8')
print(json.dumps(out['summary'],indent=2,sort_keys=True))
