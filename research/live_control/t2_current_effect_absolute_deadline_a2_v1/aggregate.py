#!/usr/bin/env python3
import argparse,json,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent)); from experiment import summarize
p=argparse.ArgumentParser(); p.add_argument('--positive',nargs=4,required=True); p.add_argument('--controls',required=True); p.add_argument('--out',required=True); a=p.parse_args()
pos=[]; hashes=[]
for i,f in enumerate(a.positive):
 raw=Path(f).read_bytes(); hashes.append(hashlib.sha256(raw).hexdigest()); r=json.loads(raw); ids=[x['case_id'] for x in r['rows']]; exp=list(range(i*8,i*8+8));
 if ids!=exp: raise SystemExit(f'positive batch{i} ids mismatch {ids} {exp}')
 pos.extend(r['rows'])
raw=Path(a.controls).read_bytes(); control_hash=hashlib.sha256(raw).hexdigest(); ctrl=json.loads(raw)['rows']
if [x['case_id'] for x in ctrl]!=list(range(32,36)): raise SystemExit('control ids mismatch')
out={'schema':2,'positive_batch_sha256':hashes,'control_batch_sha256':control_hash,'positive_rows':pos,'control_rows':ctrl,'summary':summarize(pos,ctrl)}; Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)); print(json.dumps(out['summary'],indent=2,sort_keys=True))
