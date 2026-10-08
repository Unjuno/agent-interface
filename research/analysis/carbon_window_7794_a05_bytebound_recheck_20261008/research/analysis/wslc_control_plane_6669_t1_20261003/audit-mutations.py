import json,sys,tempfile,subprocess
from pathlib import Path
aud,pressure,controls=sys.argv[1:4]
p=Path(pressure);c=Path(controls)
P=[json.loads(x) for x in p.read_text(encoding='utf-8-sig').splitlines() if x.strip()]
C=[json.loads(x) for x in c.read_text(encoding='utf-8-sig').splitlines() if x.strip()]
tests=[]
q=[x for x in P if x.get('event')!='pressure_ready']
tests.append(('false-success',q,C))
for name,fn in [('missing-stop-ack',lambda r:r.update(output='still running')),('missing-cleanup',lambda r:r.update(output='container remains'))]:
 cc=[dict(x) for x in C]
 target='list-after-stop' if name=='missing-stop-ack' else 'list-after-remove'
 fn(next(x for x in cc if x['label']==target))
 tests.append((name,P,cc))
for name,pp,cc in tests:
 with tempfile.TemporaryDirectory() as d:
  a=Path(d)/'pressure.jsonl';b=Path(d)/'controls.jsonl'
  a.write_text(''.join(json.dumps(x)+'\n' for x in pp),encoding='utf-8')
  b.write_text(''.join(json.dumps(x)+'\n' for x in cc),encoding='utf-8')
  r=subprocess.run([sys.executable,aud,str(a),str(b)],capture_output=True,text=True)
  if r.returncode==0: raise SystemExit(name+' mutation incorrectly accepted')
  print(name+': REJECTED')
