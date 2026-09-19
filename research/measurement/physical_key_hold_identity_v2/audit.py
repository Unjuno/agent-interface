from __future__ import annotations
import hashlib,json
from pathlib import Path
from corpus import SEED,CHUNKS,PER_CHUNK,LIFETIMES
HERE=Path(__file__).resolve().parent; res=json.loads((HERE/'RESULT.json').read_text()); fixed=json.loads((HERE/'results/FIXED.json').read_text()); chunks=[json.loads((HERE/'results'/f'chunk-{i:02d}.json').read_text()) for i in range(CHUNKS)]
keys=sorted(chunks[0]['counts']); totals={k:sum(x['counts'][k] for x in chunks) for k in keys};h=hashlib.sha256()
for x in chunks:h.update(f"{x['chunk']}:{x['digest_sha256']}\n".encode())
checks={'task':res.get('task')=='PHYSICAL-KEY-HOLD-ACTUATION-IDENTITY-20260917-002','seed':res.get('seed')==SEED,'chunks':res.get('chunks')==res.get('chunks_complete')==CHUNKS and all((x['chunk'],x['start'],x['end'],x['lifetimes'],x['reruns'])==(i,i*PER_CHUNK,(i+1)*PER_CHUNK,PER_CHUNK,0) for i,x in enumerate(chunks)),'lifetimes':res.get('lifetimes')==LIFETIMES,'steps':res.get('steps')==totals['steps'],'counts':res.get('counts')=={k:v for k,v in totals.items() if k!='steps'} and all(v==0 for k,v in totals.items() if k!='steps'),'fixed':fixed.get('passed') is True and res.get('fixed_controls_passed')==res.get('fixed_controls_total')==fixed.get('controls_total'),'digest':res.get('chunk_digest_sha256')==h.hexdigest(),'side_effects':all(res.get(k)==0 for k in ['x11_actions','model_calls','task_input_actions']),'reruns':res.get('reruns')==0,'decision':res.get('decision')=='PASS_PHYSICAL_HOLD_IDENTITY_CONSTRUCTION_V2_SCOPED'}
a={'passed':all(checks.values()),'checks':checks,'errors':[k for k,v in checks.items() if not v]};(HERE/'AUDIT.json').write_text(json.dumps(a,indent=2,sort_keys=True)+'\n');print(json.dumps(a,sort_keys=True))
