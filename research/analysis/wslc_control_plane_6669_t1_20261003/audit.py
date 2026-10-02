import json,sys
from pathlib import Path
p=Path(sys.argv[1]); rows=[json.loads(x) for x in p.read_text().splitlines() if x.strip()]
mode=sys.argv[2] if len(sys.argv)>2 else 'baseline'
assert rows and rows[0]['event']=='start', 'missing start'
limit=32 if mode=='baseline' else 640
for r in rows:
 assert r.get('allocated_mib',0)<=limit, 'allocation exceeds frozen maximum'
ready='baseline_ready' if mode=='baseline' else 'pressure_ready'
assert any(r['event']==ready and r.get('allocated_mib')==limit for r in rows), 'candidate did not reach frozen target'
if mode=='pressure':
 def kib(s):
  try:return int(s.split()[0])
  except:return None
 assert any(kib(r.get('meminfo',{}).get('MemAvailable',''))<128*1024 or 'some avg10=' in r.get('cgroup',{}).get('psi','') and float(r['cgroup']['psi'].split('avg10=')[1].split()[0])>0 or any(int(x.split()[1])>0 for x in r.get('cgroup',{}).get('memory.events','').splitlines() if len(x.split())==2 and x.split()[0] in ('high','max','oom','oom_kill')) for r in rows), 'pressure not evidenced'
print(json.dumps({'audit':'PASS','mode':mode,'rows':len(rows),'target_mib':limit}))
