"""Read-only exact reconstruction using the archived projector, with no GUI/model."""
import hashlib,json,tarfile,types
from pathlib import Path
root=Path(__file__).resolve().parent
sha=lambda data:hashlib.sha256(data).hexdigest()
def check(ok,message):
 if not ok:raise SystemExit(message)
manifest=json.loads((root/'manifest.json').read_text());raw={}
with tarfile.open(root/'construction.tar.gz','r:gz') as archive:
 for member in archive.getmembers():
  check(member.isfile() and member.name in manifest and member.name not in raw,'unexpected construction member')
  data=archive.extractfile(member).read();meta=manifest[member.name]
  check(len(data)==meta['bytes'] and sha(data)==meta['sha256'],'construction identity')
  raw[member.name]=data
check(set(raw)==set(manifest),'missing construction member')
module=types.ModuleType('archived_references')
exec(compile(raw['runtime/cli_v1/receipt_references.py'],'archived_references.py','exec'),module.__dict__)
summary=json.loads((root/'report.json').read_text())
source=root.parent/'guarded-mint-many-primary-02/raw.tar.gz'
check(sha(source.read_bytes())==summary['source_archive_sha256'],'source archive identity')
original_total=candidate_total=referenced=0
with tarfile.open(source,'r:gz') as archive:
 for n,expected in enumerate(summary['rows'],1):
  data=archive.extractfile(f'results-local/guarded-mint-many-primary-02/transport/reply-{n}.json').read()
  text=json.loads(data)['result']['content'][0]['text'];view=json.loads(text)
  compact=module.compact_guarded_observation(view)
  check(module.expand_guarded_observation(compact)==view,'exact reconstruction')
  check(json.dumps(view,allow_nan=False)==text,'original serialization')
  output=json.dumps(compact,allow_nan=False)
  row={'attempt':n,'reply_sha256':sha(data),'original_utf8_bytes':len(text.encode()),'candidate_utf8_bytes':len(output.encode()),'referenced':'reference_schema' in compact,'exact_roundtrip':True}
  check(row==expected,'measurement mismatch')
  original_total+=row['original_utf8_bytes'];candidate_total+=row['candidate_utf8_bytes'];referenced+=row['referenced']
check(len(summary['rows'])==30 and (original_total,candidate_total,referenced)==(summary['original_utf8_bytes'],summary['candidate_utf8_bytes'],summary['referenced_reports']),'summary mismatch')
checks=json.loads(raw['results-local/guarded-observation-refs-check-01/result.json'])
check(checks['status']=='PASS' and all(s['returncode']==0 for s in checks['suites']),'checks failed')
print(json.dumps({'status':'PASS','scope':summary['scope'],'original_utf8_bytes':original_total,'candidate_utf8_bytes':candidate_total,'referenced_reports':referenced,'actual_model_tokens':'not measured','live_candidate_use':'not yet performed'},indent=2))
