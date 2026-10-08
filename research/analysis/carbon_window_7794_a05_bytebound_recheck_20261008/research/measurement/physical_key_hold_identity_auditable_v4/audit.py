from __future__ import annotations
import hashlib,json
from pathlib import Path
from corpus import CHUNKS,LIFETIMES,PER_CHUNK,SEED
HERE=Path(__file__).resolve().parent
EXPECTED_MODEL_BLOB='bdf68b88111ddb61297cdec29be394d7fd4dd060'; EXPECTED_ORACLE_BLOB='48aa8adc6c2c28d1e2e01fe17d2e2ab8b37bf49d'
def git_blob(p):
 b=p.read_bytes(); return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def validate(chunks_doc=None,result=None,fixed=None):
 chunks_doc=chunks_doc or json.loads((HERE/'CHUNK_SUMMARIES.json').read_text()); result=result or json.loads((HERE/'RESULT.json').read_text()); fixed=fixed or json.loads((HERE/'FIXED.json').read_text()); chunks=chunks_doc.get('chunks',[]); c={}
 c['science_model_blob']=git_blob(HERE/'model.py')==EXPECTED_MODEL_BLOB; c['science_oracle_blob']=git_blob(HERE/'oracle.py')==EXPECTED_ORACLE_BLOB
 c['chunk_count']=len(chunks)==CHUNKS and [x.get('chunk') for x in chunks]==list(range(CHUNKS)); c['schedule']=c['chunk_count'] and all((x['start'],x['end'],x['lifetimes'],x['reruns'])==(i*PER_CHUNK,(i+1)*PER_CHUNK,PER_CHUNK,0) for i,x in enumerate(chunks))
 keys=sorted(chunks[0]['counts']) if chunks else []; totals={k:sum(x['counts'][k] for x in chunks) for k in keys}; h=hashlib.sha256()
 for x in chunks: h.update(f"{x['chunk']}:{x['digest_sha256']}\n".encode())
 c['lifetimes']=sum(x.get('lifetimes',0) for x in chunks)==LIFETIMES==result.get('lifetimes'); c['steps']=result.get('steps')==totals.get('steps'); c['zero_fail_counts']=all(v==0 for k,v in totals.items() if k!='steps') and result.get('counts')=={k:v for k,v in totals.items() if k!='steps'}; c['digest']=result.get('chunk_digest_sha256')==h.hexdigest(); c['fixed']=fixed.get('passed') is True and fixed.get('controls_passed')==fixed.get('controls_total')==13 and result.get('fixed_controls_passed')==result.get('fixed_controls_total')==13; c['seed']=result.get('seed')==SEED; c['reruns']=result.get('reruns')==0; c['side_effects']=all(result.get(k)==0 for k in ('x11_actions','model_calls','task_input_actions')); c['decision']=result.get('decision')=='PASS_PHYSICAL_HOLD_IDENTITY_AUDITABLE_V4_SCOPED'
 return {'passed':all(c.values()),'checks':c,'errors':[k for k,v in c.items() if not v]}
def main():
 out=validate(); out['source_sha256']={p:hashlib.sha256((HERE/p).read_bytes()).hexdigest() for p in ['model.py','oracle.py','corpus.py','fixed_controls.py','run_chunk.py','aggregate.py','audit.py','corruption_controls.py','FREEZE.json','PLAN.md']}; (HERE/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True))
if __name__=='__main__': main()
