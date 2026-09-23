import base64,pathlib,hashlib
root=pathlib.Path(__file__).resolve().parent
s=''.join((root/'source_chunks'/f'{i:02d}.b64').read_text() for i in range(4))
raw=base64.b64decode(s)
want='c66163f8f28bd0f8e3328447f3a0962ea18c7d026e81ce1e525d7d46eefe31f7'
got=hashlib.sha256(raw).hexdigest()
if got!=want: raise SystemExit(got)
(root/'experiment.py').write_bytes(raw)
print(got)
