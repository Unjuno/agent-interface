"""Independent audit of the retained V39 frame-signal boundary result."""
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
RAW = json.loads((HERE / "raw.json").read_text(encoding="utf-8"))


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True,
                          capture_output=True).stdout


assert RAW["experiment_id"] == FREEZE["experiment_id"]
assert RAW["source_commit"] == FREEZE["source_commit"]
assert RAW["source_blob"] == FREEZE["source_blob"]
assert git("rev-parse", f"{RAW['source_commit']}:{FREEZE['source_path']}").decode().strip() == RAW["source_blob"]
source = git("show", f"{RAW['source_commit']}:{FREEZE['source_path']}")
assert hashlib.sha256(source).hexdigest() == RAW["source_sha256"]
assert hashlib.sha256((HERE / "run_probe.py").read_bytes()).hexdigest() == RAW["runner_sha256"]

inputs = RAW["inputs"]
assert inputs["baseline_sequence"] < inputs["changed_sequence"]
assert inputs["baseline_capture_ns"] < inputs["changed_capture_ns"]
assert inputs["health_values"] == [84, 84]
assert inputs["ammo_values"] == [37, 37]
assert inputs["frame_hashes"][0] != inputs["frame_hashes"][1]
assert inputs["binding_unchanged"] is True
assert RAW["monitor_outputs"] == {"baseline": None, "changed_frame": None}
assert RAW["decision"] == "FAIL"
assert "synthetic" in RAW["scope"]

print(json.dumps({
    "passed": True,
    "source_commit": RAW["source_commit"],
    "source_blob": RAW["source_blob"],
    "source_sha256": RAW["source_sha256"],
    "runner_sha256": RAW["runner_sha256"],
    "decision": RAW["decision"],
    "scope": RAW["scope"],
}, indent=2))
