import base64, hashlib, pathlib
HERE = pathlib.Path(__file__).resolve().parent
EXPECTED = '8053114c17a666043f9698e36e2e69676955a1987043b8037a7511c19e5273ba'
parts = [HERE / f'source-freeze.chunk{i:02d}.b64' for i in range(1, 11)]
text = ''.join(p.read_text().strip() for p in parts)
data = base64.b64decode(text, validate=True)
actual = hashlib.sha256(data).hexdigest()
if actual != EXPECTED:
    raise SystemExit(f'SHA256 mismatch: {actual}')
out = HERE / 'source-freeze.tar.gz'
if out.exists():
    raise SystemExit(f'refusing existing output: {out}')
out.write_bytes(data)
print(f'PASS {len(data)} {actual} {out}')
