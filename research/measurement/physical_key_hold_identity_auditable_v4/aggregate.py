from __future__ import annotations
import hashlib,json
from pathlib import Path
from corpus import CHUNKS,LIFETIMES,PER_CHUNK,SEED
HERE=Path(__file__).resolve().parent

def main():
    chunks=json.loads((HERE/'CHUNK_SUMMARIES.json').read_text())['chunks']; fixed=json.loads((HERE/'FIXED.json').read_text()); errors=[]
    if len(chunks)!=CHUNKS: errors.append('chunk_count')
    if [x.get('chunk') for x in chunks]!=list(range(CHUNKS)): errors.append('chunk_order')
    if any((x.get('start'),x.get('end'),x.get('lifetimes'),x.get('reruns'))!=(i*PER_CHUNK,(i+1)*PER_CHUNK,PER_CHUNK,0) for i,x in enumerate(chunks)): errors.append('chunk_schedule')
    keys=sorted(chunks[0]['counts']) if chunks else []; totals={k:sum(x['counts'][k] for x in chunks) for k in keys}; h=hashlib.sha256()
    for x in chunks: h.update(f"{x['chunk']}:{x['digest_sha256']}\n".encode())
    bad={k:v for k,v in totals.items() if k!='steps' and v!=0}
    if bad: errors.append('nonzero_counts:'+repr(bad))
    if sum(x['lifetimes'] for x in chunks)!=LIFETIMES: errors.append('lifetimes')
    if not fixed.get('passed') or fixed.get('controls_passed')!=fixed.get('controls_total') or fixed.get('controls_total')!=13: errors.append('fixed')
    result={'task':'PHYSICAL-KEY-HOLD-ACTUATION-IDENTITY-AUDITABLE-20260918-004','decision':'PASS_PHYSICAL_HOLD_IDENTITY_AUDITABLE_V4_SCOPED' if not errors else 'FAIL_CONSTRUCTION','seed':SEED,'chunks':CHUNKS,'chunks_complete':len(chunks),'lifetimes':sum(x['lifetimes'] for x in chunks),'steps':totals.get('steps',0),'counts':{k:v for k,v in totals.items() if k!='steps'},'fixed_controls_passed':fixed.get('controls_passed'),'fixed_controls_total':fixed.get('controls_total'),'chunk_digest_sha256':h.hexdigest(),'reruns':0,'x11_actions':0,'model_calls':0,'task_input_actions':0,'errors':errors}
    (HERE/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
