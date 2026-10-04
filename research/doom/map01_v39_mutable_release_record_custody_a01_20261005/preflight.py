"""No-input source/image/output preflight for A01."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == "4a8049327eb44b54cfcf55167adb102a710a7051"
assert not (HERE / "results/formal_01/candidate.json").exists()
assert not (HERE / "results/formal_02/candidate.json").exists()
expected = {
    "input_owner_v13_candidate.py": "0e3c65aadfba76b644f1ca99afa267bc873bc120320a4b0cac67dafb82cfa814",
    "bridge_v2_candidate.py": "81e759b0484ac5b7854da0ebcffa917035f56b83a3dbfda40cafbb7f9f5138d1",
}
src = ROOT / "research/doom/map01_v39_expiry_pending_owner_current_a03_20261005/candidate_source"
for name, digest in expected.items():
    assert hashlib.sha256((src / name).read_bytes()).hexdigest() == digest
image = subprocess.check_output(
    ["docker", "image", "inspect", "python:3.12.11-slim", "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"],
    text=True,
).strip()
assert image == "sha256:47ae396f09c1303b8653019811a8498470603d7ffefc29cb07c88f1f8cb3d19f linux/arm64", image
assert json.loads((ROOT / "research/doom/map01_v39_expiry_pending_owner_current_a03_20261005/SOURCE_LOCK.json").read_text())
print("PREFLIGHT_OK_FROZEN_SOURCE_IMAGE_NO_OUTPUT_NO_INPUT")
