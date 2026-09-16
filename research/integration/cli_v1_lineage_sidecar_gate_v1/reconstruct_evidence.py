import base64, hashlib, pathlib, sys
root=pathlib.Path(__file__).parent
parts=[root/f'evidence.part{i:02d}.b64' for i in range(3)]
raw=base64.b64decode(''.join(p.read_text() for p in parts))
want='4e800dc59dba8dfadd169b6a5587c0185a38acb1d3ccba7b8e3b5cca39a7d713'
got=hashlib.sha256(raw).hexdigest()
if got!=want: raise SystemExit(f'SHA256 mismatch: {got}')
out=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else root/'evidence.tar.xz'
out.write_bytes(raw)
print(f'{out} {len(raw)} {got}')
