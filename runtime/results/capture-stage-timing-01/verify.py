from pathlib import Path
import hashlib,json,tarfile
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text())
with tarfile.open(root/'raw.tar.gz','r:gz') as tar:
 members={m.name:m for m in tar.getmembers()}
 assert set(members)==set(manifest['files'])
 def read(name): return tar.extractfile(members[name]).read()
 for name,digest in manifest['files'].items():
  assert hashlib.sha256(read(name)).hexdigest()==digest,name
 prefix='results-local/capture-stage-timing-live-05/'
 reports=[n for n in members if n.startswith(prefix+'bridge/observation-')]
 assert len(reports)==5
 for name in reports:
  o=json.loads(read(name));t=o['timing_ns'];native=o['native'];a=native['artifact'];v=a['timing_ns']
  assert list(t.values())==sorted(t.values())
  assert list(v.values())==sorted(v.values())
  assert t['started']<=native['capture_started_ns']<=native['capture_ended_ns']<=v['started']<=v['hashed']<=t['public_returned']
  image=prefix+'bridge/images/'+Path(a['path']).name
  assert hashlib.sha256(read(image)).hexdigest()==a['sha256']
  assert a['source_raw_sha256']==native['sha256']
 print('PASS:',len(members),'retained files; five ordered observations with image identities')
