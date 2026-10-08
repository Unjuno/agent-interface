import hashlib,json,tarfile
from pathlib import Path
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text())
with tarfile.open(root/'raw.tar.gz','r:gz') as archive:
 members=archive.getmembers()
 if len(members)!=len(manifest) or len({m.name for m in members})!=len(members):
  raise SystemExit('member count or duplicate mismatch')
 for member in members:
  if not member.isfile() or member.name not in manifest:raise SystemExit('unexpected member')
  data=archive.extractfile(member).read(); expected=manifest[member.name]
  if len(data)!=expected['bytes'] or hashlib.sha256(data).hexdigest()!=expected['sha256']:
   raise SystemExit('integrity mismatch: '+member.name)
summary=json.loads((root/'summary.json').read_text())
if summary['status']!='INTERRUPTED_NOT_SUCCESS' or summary['success_claim']:
 raise SystemExit('interrupted evidence must not claim success')
print(f"PASS: {len(manifest)} retained files; interrupted trial, not success")