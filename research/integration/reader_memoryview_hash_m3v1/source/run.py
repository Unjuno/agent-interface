import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path
from common import corpus_bytes, sha256_bytes, sha256_path

p=argparse.ArgumentParser(); p.add_argument('--phase',choices=['construction','formal'],required=True); p.add_argument('--out',required=True); a=p.parse_args()
root=Path(__file__).resolve().parent; out=Path(a.out)
if out.exists(): raise SystemExit('OUTPUT_EXISTS')
out.mkdir(parents=True); started=time.time_ns(); (out/'STARTED').write_text(str(started)+'\n')
records=64 if a.phase=='construction' else 4096; cursors=[0,32,64] if a.phase=='construction' else [0,2048,4064,4096]; reps=1 if a.phase=='construction' else 3
corpus=out/'corpus.jsonl'; data=corpus_bytes(records); corpus.write_bytes(data)
resource=[]
for cur in cursors:
  for rep in range(reps):
    order=['BASELINE','MEMORYVIEW'] if rep%2==0 else ['MEMORYVIEW','BASELINE']
    for arm in order:
      cmd=[sys.executable,'-B',str(root/'worker.py'),'--arm',arm,'--corpus',str(corpus),'--cursor-records',str(cur),'--max-records','32']
      cp=subprocess.run(cmd,capture_output=True,text=True,timeout=8)
      rec={'kind':'resource','cursor_records':cur,'rep':rep,'arm':arm,'argv':cmd,'exit':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr}
      resource.append(rec)
      if cp.returncode!=0: break
    if resource[-1]['exit']!=0: break
  if resource[-1]['exit']!=0: break
contracts=[]
if all(x['exit']==0 for x in resource):
  for arm in ['BASELINE','MEMORYVIEW']:
    cmd=[sys.executable,'-B',str(root/'contract_worker.py'),'--arm',arm]; cp=subprocess.run(cmd,capture_output=True,text=True,timeout=8)
    contracts.append({'kind':'contract','arm':arm,'argv':cmd,'exit':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr})
summary={'schema':'reader-memoryview-run-v1','phase':a.phase,'records':records,'corpus_bytes':len(data),'corpus_sha256':sha256_bytes(data),'resource':resource,'contracts':contracts,'started_ns':started,'ended_ns':time.time_ns(),'runner_pid':os.getpid(),
'source_sha256':{x:sha256_path(root/x) for x in ['baseline_reader.py','candidate_reader.py','common.py','worker.py','contract_worker.py','run.py']}}
(out/'RAW.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
print(json.dumps({'phase':a.phase,'resource_rows':len(resource),'contracts':len(contracts),'all_exit_zero':all(x['exit']==0 for x in resource+contracts),'raw_sha256':sha256_path(out/'RAW.json')},sort_keys=True))
raise SystemExit(0 if all(x['exit']==0 for x in resource+contracts) and len(resource)==len(cursors)*reps*2 and len(contracts)==2 else 2)
