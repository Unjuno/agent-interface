import base64, pathlib, hashlib, sys
root=pathlib.Path(__file__).resolve().parent
raw=base64.b64decode((root/"source_bundle.b64").read_text().strip())
sha=hashlib.sha256(raw).hexdigest()
expected="6da07134aea7d65a328548e4aa5cc91c6ec34a7c47eb7ad8ae12ab34bf73124c"
if sha!=expected:
    raise SystemExit(f"source hash mismatch {sha}")
out=root/"experiment.py"
out.write_bytes(raw)
print(out, sha)
