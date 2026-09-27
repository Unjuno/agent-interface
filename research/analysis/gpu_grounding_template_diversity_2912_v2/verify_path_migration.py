"""Verify path migration without rerunning or rewriting the frozen study."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
manifest=json.loads((root/'PATH_MIGRATION.json').read_text())
seen=set()
for row in manifest['files']:
 original=row['original']; replacement=row['replacement']
 assert '\\' in original and replacement==original.replace('\\','/')
 assert replacement not in seen;seen.add(replacement)
 p=(root/replacement).resolve()
 assert p.is_relative_to(root)
 data=p.read_bytes()
 assert len(data)==row['bytes']
 assert hashlib.sha256(data).hexdigest()==row['sha256']
 assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==row['git_blob']
for name,digest in manifest['unchanged_files'].items():
 p=(root/name).resolve();assert p.is_relative_to(root)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,name
assert len(seen)==48
print('PASS: 48 byte-identical migrated images; 21 original study files unchanged')
