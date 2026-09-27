"""Read-only formal preflight. The runner is never invoked from this file."""
import hashlib, json, os
from pathlib import Path

def sha(data): return hashlib.sha256(data).hexdigest()

freeze_bytes=Path("/freeze.json").read_bytes()
manifest_bytes=Path("/source_manifest.json").read_bytes()
prereg_bytes=Path("/preregistration.md").read_bytes()
freeze=json.loads(freeze_bytes); manifest=json.loads(manifest_bytes)
assert sha(manifest_bytes)==os.environ["SOURCE_MANIFEST_SHA256"]==freeze["source_manifest_sha256"]
assert sha(freeze_bytes)==os.environ["FREEZE_SHA256"]
assert sha(prereg_bytes)==os.environ["PREREGISTRATION_SHA256"]==freeze["preregistration_sha256"]
assert freeze["source_commit"]==os.environ["FROZEN_SOURCE_COMMIT"]==manifest["source_commit"]
for rel, expected in manifest["files"].items():
    path=Path("/src")/rel
    assert path.is_file(), f"missing source mount: {rel}"
    assert sha(path.read_bytes())==expected, f"source hash mismatch: {rel}"
assert freeze["image_id"]=="sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27"
assert freeze["platform"]=="linux/arm64"
result={"preflight":"PASS","source_files":len(manifest["files"]),
        "source_commit":freeze["source_commit"],"preregistration_sha256":sha(prereg_bytes)}
Path(os.environ["PREFLIGHT_OUTPUT"]).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps(result,sort_keys=True))
