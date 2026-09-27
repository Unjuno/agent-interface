from __future__ import annotations
import hashlib,json
from pathlib import Path
from corpus import SEED,CHUNKS,PER_CHUNK,LIFETIMES
HERE=Path(__file__).resolve().parent; results=HERE/'results'; out=HERE/'RESULT.json'
if out.exists(): raise RuntimeError('RESULT exists; reaggregation forbidden')
fixed=json.loads((results/'FIXED.json').read_text()); chunks=[]
for i in range(CHUNKS):
 p=results/f'chunk-{i:02d}.json'
 if not p.exists(): raise RuntimeError(f'missing chunk {i}')
 x=json.loads(p.read_text())
 if (x['chunk'],x['start'],x['end'],x['lifetimes'],x['seed'],x['reruns'])!=(i,i*PER_CHUNK,(i+1)*PER_CHUNK,PER_CHUNK,SEED,0): raise RuntimeError(f'chunk identity {i}')
 chunks.append(x)
count_keys=sorted(chunks[0]['counts']); totals={k:sum(x['counts'][k] for x in chunks) for k in count_keys}
h=hashlib.sha256()
for x in chunks: h.update(f"{x['chunk']}:{x['digest_sha256']}\n".encode())
passed=(fixed['passed'] and sum(x['lifetimes'] for x in chunks)==LIFETIMES and all(totals[k]==0 for k in count_keys if k!='steps'))
r={'schema':'physical_key_hold_identity_result_v2','task':'PHYSICAL-KEY-HOLD-ACTUATION-IDENTITY-20260917-002','seed':SEED,'chunks':CHUNKS,'chunks_complete':len(chunks),'lifetimes':sum(x['lifetimes'] for x in chunks),'steps':totals.pop('steps'),'counts':totals,'fixed_controls_passed':fixed['controls_passed'],'fixed_controls_total':fixed['controls_total'],'chunk_digest_sha256':h.hexdigest(),'reruns':0,'x11_actions':0,'model_calls':0,'task_input_actions':0,'decision':'PASS_PHYSICAL_HOLD_IDENTITY_CONSTRUCTION_V2_SCOPED' if passed else 'FAIL_PHYSICAL_HOLD_IDENTITY_CONSTRUCTION_V2'}
out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,sort_keys=True))
