import base64, hashlib, pathlib, sys
EXPECTED='f115112cc18c7ab526980292b5cc8697ff0296ac8a9cc724fe6ceaf39a954289'
root=pathlib.Path(__file__).resolve().parent
parts=sorted(root.glob('evidence.tar.gz.b64.part-*'))
if not parts:
    raise SystemExit('no evidence parts')
raw=base64.b64decode(b''.join(p.read_bytes() for p in parts), validate=True)
got=hashlib.sha256(raw).hexdigest()
if got != EXPECTED:
    raise SystemExit(f'sha256 mismatch: {got}')
out=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'evidence.tar.gz')
if out.exists():
    raise SystemExit(f'refusing to overwrite {out}')
out.write_bytes(raw)
print(f'PASS_RECONSTRUCT {len(raw)} bytes sha256={got}')
