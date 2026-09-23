"""Descriptive cProfile of existing store; static state, no transport or GUI action."""
import cProfile,hashlib,json,pstats,tempfile,time
from pathlib import Path
from durable_submit_v3 import store
HERE=Path(__file__).resolve().parent
root=HERE/'results/journal-store-profile-01';root.mkdir(exist_ok=False)
source=HERE/'results/journal-location-01/02-native/journal.json'
state=json.loads(source.read_text());records=[]
for mode in ['mounted','native','native','mounted']:
 with tempfile.TemporaryDirectory(prefix='store-profile-',dir=str(root) if mode=='mounted' else None) as folder:
  p=Path(folder)/'journal.json';profile=cProfile.Profile();begin=time.perf_counter_ns()
  profile.enable()
  for _ in range(8):store(p,state)
  profile.disable();elapsed=time.perf_counter_ns()-begin
  stats=pstats.Stats(profile)
  functions=[{'file':k[0],'line':k[1],'function':k[2],'primitive_calls':v[0],'calls':v[1],'self_seconds':v[2],'cumulative_seconds':v[3]} for k,v in stats.stats.items()]
  records.append({'mode':mode,'store_calls':8,'wall_ms':elapsed/1e6,'functions':sorted(functions,key=lambda x:x['cumulative_seconds'],reverse=True)})
report={'scope':'static journal store profiling, eight stores per arm ABBA; profiler overhead; not live caller/model benchmark', 'state_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_sha256':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['profile_journal_store_v1.py','durable_submit_v3.py']},'runs':records}
(root/'profile.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps([{'mode':r['mode'],'wall_ms':r['wall_ms'],'top':r['functions'][:7]} for r in records],indent=2))
