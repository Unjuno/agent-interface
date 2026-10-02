import hashlib,json,tarfile,tempfile
from pathlib import Path
from audit_pair import audit,require,read
def verify():
 here=Path(__file__).resolve().parent
 manifest=read(here/'raw-manifest.json')
 with tempfile.TemporaryDirectory(prefix='production-spine-audit-') as tmp:
  root=Path(tmp)
  with tarfile.open(here/'raw.tar.gz','r:gz') as archive:
   members=archive.getmembers()
   require(len(members)==len(manifest) and len({m.name for m in members})==len(members),'exact archive members')
   for m in members:
    p=Path(m.name)
    require(m.isfile() and not p.is_absolute() and '..' not in p.parts and m.name in manifest,'safe retained member')
    raw=archive.extractfile(m).read();entry=manifest[m.name]
    require(len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256'],'retained bytes '+m.name)
    dest=root/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
  pair=audit(root/'production-spine-02')
  failed=root/'production-spine-01';session=failed/'guarded-local/session';host=failed/'guarded-local/host'
  plan=read(failed/'PLAN.json')
  for name,sha in plan['hashes'].items():require(hashlib.sha256((failed/name).read_bytes()).hexdigest()==sha,'failed frozen bytes')
  score=read(session/'evaluation-at-close.json');terminal=read(session/'finish.json')
  require(score['success'] is False and score['record_count']==0 and len(score['missing'])==6,'failed original denominator')
  require(terminal['primary_state']['stopped']=='invalid primary review arguments' and terminal['host_exit']['code']==0,'failed original terminal')
  requests=[read(p) for p in host.glob('request-*.json')]
  require(not any(q['tool'] in ['interface_dispatch','interface_guarded_input'] for q in requests),'failed before input')
  pair['prior_failed_allocation']={'seed':plan['seed'],'tasks_successful':0,'tasks_allocated':6,'calls':len(requests),'stop':terminal['primary_state']['stopped']}
  pair['raw_files']=len(manifest)
  pair['archive_sha256']=hashlib.sha256((here/'raw.tar.gz').read_bytes()).hexdigest()
  return pair
if __name__=='__main__':print(json.dumps(verify(),indent=2))
