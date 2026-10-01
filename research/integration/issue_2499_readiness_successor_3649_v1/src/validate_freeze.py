import hashlib,json,os
from pathlib import Path

def sha(data): return hashlib.sha256(data).hexdigest()
freeze_bytes=Path("/freeze.json").read_bytes(); manifest_bytes=Path("/source_manifest.json").read_bytes(); prereg=Path("/preregistration.md").read_bytes()
freeze=json.loads(freeze_bytes); manifest=json.loads(manifest_bytes)
assert sha(manifest_bytes)==os.environ["SOURCE_MANIFEST_SHA256"]==freeze["source_manifest_sha256"]
assert sha(freeze_bytes)==os.environ["FREEZE_SHA256"]
assert sha(prereg)==os.environ["PREREGISTRATION_SHA256"]==freeze["preregistration_sha256"]
assert freeze["source_commit"]==manifest["source_commit"]==os.environ["FROZEN_SOURCE_COMMIT"]
assert freeze["image_id"]==os.environ["PINNED_IMAGE_ID"]
assert freeze["platform"]=="linux/arm64"
for name,digest in manifest["files"].items():
    p=Path("/src")/name
    assert p.is_file() and sha(p.read_bytes())==digest, name
print(json.dumps({"decision":"PASS_FREEZE_INTEGRITY","source_files":len(manifest["files"]),"source_commit":freeze["source_commit"]},sort_keys=True))
