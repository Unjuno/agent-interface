import base64,pathlib,hashlib
root=pathlib.Path(__file__).resolve().parent
s=''.join((root/'source_chunks'/f'{i:02d}.b64').read_text() for i in range(6))
raw=base64.b64decode(s)
want='302744699cb6b9a6db9cff1890a804c6c2f51deedb8113c180ba44fe5ee889e8'
got=hashlib.sha256(raw).hexdigest()
if got!=want: raise SystemExit(got)
(root/'experiment.py').write_bytes(raw)
print(got)
