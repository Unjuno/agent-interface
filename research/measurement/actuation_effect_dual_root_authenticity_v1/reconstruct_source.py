import base64,pathlib,hashlib
root=pathlib.Path(__file__).resolve().parent
s=''.join((root/'source_chunks'/f'{i:02d}.b64').read_text() for i in range(6))
raw=base64.b64decode(s)
want='d47171db2b631b36aeb2d15045eff704afaf5cb5e47e46d86f206409e32999d5'
got=hashlib.sha256(raw).hexdigest()
if got!=want: raise SystemExit(got)
(root/'experiment.py').write_bytes(raw)
print(got)
