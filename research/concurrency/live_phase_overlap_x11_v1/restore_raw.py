import base64,gzip,hashlib,pathlib
root=pathlib.Path(__file__).parent
b64=(root/"RAW_CASES.json.gz.b64").read_text().strip()
raw=gzip.decompress(base64.b64decode(b64))
expected="8dc12b19e94b0cbd20e169073272fc3a512fef3ee66100360e2f6f30656badd5"
actual=hashlib.sha256(raw).hexdigest()
if actual!=expected: raise SystemExit(f"sha256 mismatch: {actual}")
(root/"RAW_CASES.json").write_bytes(raw)
print(actual)
