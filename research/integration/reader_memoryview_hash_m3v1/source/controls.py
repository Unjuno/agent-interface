import argparse, copy, json, subprocess, sys, tempfile
from pathlib import Path

def mutate(raw,name):
 r=copy.deepcopy(raw)
 if name=='drop': r['resource'].pop()
 elif name=='duplicate': r['resource'].append(copy.deepcopy(r['resource'][0]))
 elif name=='arm': r['resource'][0]['arm']='MEMORYVIEW' if r['resource'][0]['arm']=='BASELINE' else 'BASELINE'
 elif name=='cursor': r['resource'][0]['cursor_records']=123
 elif name=='source':
  x=json.loads(r['resource'][0]['stdout']); x['source_sha256']='0'*64; r['resource'][0]['stdout']=json.dumps(x,separators=(',',':'))+'\n'
 elif name=='result':
  x=json.loads(r['resource'][0]['stdout']); x['result']['authority']='task'; r['resource'][0]['stdout']=json.dumps(x,separators=(',',':'))+'\n'
 elif name=='inputsha':
  x=json.loads(r['resource'][0]['stdout']); x['input_sha256_after']='0'*64; r['resource'][0]['stdout']=json.dumps(x,separators=(',',':'))+'\n'
 elif name=='exit': r['resource'][0]['exit']=7
 elif name=='corpussha': r['corpus_sha256']='0'*64
 elif name=='contract':
  x=json.loads(r['contracts'][0]['stdout']); x['rows'][0][1]['kind']='error'; x['rows'][0][1]['message']='MUTATED'; r['contracts'][0]['stdout']=json.dumps(x,separators=(',',':'))+'\n'
 return r
p=argparse.ArgumentParser(); p.add_argument('raw'); p.add_argument('--audit',required=True); a=p.parse_args(); raw=json.loads(Path(a.raw).read_text()); names=['drop','duplicate','arm','cursor','source','result','inputsha','exit','corpussha','contract']; rows=[]
for name in names:
 with tempfile.TemporaryDirectory() as td:
  q=Path(td)/'RAW.json'; q.write_text(json.dumps(mutate(raw,name),sort_keys=True,indent=2)+'\n'); (Path(td)/'corpus.jsonl').write_bytes((Path(a.raw).parent/'corpus.jsonl').read_bytes())
  cp=subprocess.run([sys.executable,'-B',a.audit,str(q)],capture_output=True,text=True)
  rows.append({'name':name,'rejected':cp.returncode!=0,'exit':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr})
print(json.dumps({'schema':'reader-memoryview-controls-v1','rows':rows,'all_rejected':all(x['rejected'] for x in rows)},sort_keys=True,indent=2)); raise SystemExit(0 if all(x['rejected'] for x in rows) else 1)
