import base64,gzip,hashlib,pathlib
root=pathlib.Path(__file__).parent
raw=gzip.decompress(base64.b64decode((root/'RAW_CASES.json.gz.b64').read_bytes()))
expected='6426b6425764adc585585eff915faea504d1ddabac38ae34720660e277ce37f8'
got=hashlib.sha256(raw).hexdigest()
if got!=expected: raise SystemExit(f'raw sha mismatch: {got}')
(root/'RAW_CASES.json').write_bytes(raw)
print(got)
