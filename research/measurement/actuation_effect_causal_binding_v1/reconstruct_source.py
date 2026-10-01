import base64,pathlib,hashlib
root=pathlib.Path(__file__).resolve().parent
s=''.join((root/'source_chunks'/f'{i:02d}.b64').read_text() for i in range(5))
raw=base64.b64decode(s)
want='90430f5e98acf47d18e614abf9a2785f511297be4a1e127ede0e4d40052e87ae'
got=hashlib.sha256(raw).hexdigest()
if got!=want: raise SystemExit(got)
(root/'experiment.py').write_bytes(raw)
print(got)
