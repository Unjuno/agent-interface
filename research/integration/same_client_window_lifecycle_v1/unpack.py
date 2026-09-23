"""Verify and extract the Issue 3950 evidence bundle. Never executes a study."""
from __future__ import annotations
import base64, hashlib, io, json, lzma, pathlib, sys, tarfile

EXPECTED = '1b7d62ae6549b77d7cbcc672ba94728dfb7b09bf6331670e534635d378a597c5'
root = pathlib.Path(__file__).resolve().parent
if len(sys.argv) != 2:
    raise SystemExit('Usage: python unpack.py NEW_DIRECTORY')
out = pathlib.Path(sys.argv[1]).resolve()
if out.exists():
    raise SystemExit('Refusing to overwrite an existing directory')
parts = [root / f'bundle.part{i:02}.b64' for i in range(1, 5)]
encoded = ''.join(''.join(p.read_text().split()) for p in parts)
compressed = base64.b64decode(encoded, validate=True)
if hashlib.sha256(compressed).hexdigest() != EXPECTED:
    raise SystemExit('Bundle SHA256 mismatch')
raw = lzma.decompress(compressed, memlimit=128 * 1024 * 1024)
if len(raw) > 2 * 1024 * 1024:
    raise SystemExit('Unexpected archive size')
files = {}
with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
    for member in archive.getmembers():
        rel = pathlib.PurePosixPath(member.name)
        if (not member.isfile() or rel.is_absolute() or '..' in rel.parts
                or member.name in files or len(files) >= 128):
            raise SystemExit('Unsafe or duplicate archive entry')
        files[member.name] = archive.extractfile(member).read()
manifest = json.loads(files['MANIFEST.json'])
if set(files) != set(manifest) | {'MANIFEST.json'}:
    raise SystemExit('Manifest inventory mismatch')
for name, item in manifest.items():
    data = files[name]
    if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
        raise SystemExit('File integrity mismatch: ' + name)
out.mkdir(parents=True, exist_ok=False)
for name, data in files.items():
    target = out.joinpath(*pathlib.PurePosixPath(name).parts)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(data)
print(json.dumps({'extracted_files':len(files),'verified_files':len(manifest),
                  'bundle_sha256':EXPECTED,'destination':str(out),'executed_study':False}))
