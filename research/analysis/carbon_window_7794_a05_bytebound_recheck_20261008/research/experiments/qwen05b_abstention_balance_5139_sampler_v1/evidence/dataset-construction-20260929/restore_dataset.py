import base64, gzip, hashlib
from pathlib import Path
encoded = Path("dataset.json.gz.b64").read_bytes()
raw = gzip.decompress(base64.b64decode(encoded, validate=True))
expected_size = 803928
expected_sha = "d96c4072db2ee3bb1af7503a8ae98e062794072385a15099f32121a7a8caad4b"
if len(raw) != expected_size or hashlib.sha256(raw).hexdigest() != expected_sha:
    raise SystemExit("STOP_DATASET_CAPSULE_IDENTITY")
Path("restored_dataset.json").write_bytes(raw)
print(f"PASS restore bytes={len(raw)} sha256={expected_sha}")

