import json,sys,tempfile,subprocess
from pathlib import Path
aud,pressure,controls,baseline,bcontrols=sys.argv[1:6]
def read(p):return [json.loads(x) for x in Path(p).read_text(encoding='utf-8-sig').splitlines() if x.strip()]
P,C,B,BC=map(read,(pressure,controls,baseline,bcontrols))
tests=[('false-success',[x for x in P if x.get('event')!='pressure_ready'],C)]
for name,target,value in [('missing-stop-ack','list-after-stop','still running'),('missing-cleanup','list-after-remove','container remains')]:
 cc=[dict(x) for x in C];next(x for x in cc if x['label']==target)['output']=value
 tests.append((name,P,cc))
for name,pp,cc in tests:
 with tempfile.TemporaryDirectory() as d:
  paths=[Path(d)/n for n in ('pressure.jsonl','controls.jsonl','baseline.jsonl','baseline-controls.jsonl')]
  for path,rows in zip(paths,(pp,cc,B,BC)):path.write_text(''.join(json.dumps(x)+'\n' for x in rows),encoding='utf-8')
  r=subprocess.run([sys.executable,aud,*map(str,paths)],capture_output=True,text=True)
  if r.returncode==0:raise SystemExit(name+' mutation incorrectly accepted')
  print(name+': REJECTED')
