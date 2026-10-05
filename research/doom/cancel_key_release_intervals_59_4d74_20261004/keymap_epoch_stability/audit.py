"""Check the saved synthetic remap result without rerunning the owner."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FREEZE = json.loads((ROOT / "FREEZE.json").read_text())
RESULT = json.loads((ROOT / "RESULT.json").read_text())

def sha(data):
    return hashlib.sha256(data).hexdigest()

source = subprocess.check_output([
    "git", "show", f"{FREEZE['source_commit']}:{FREEZE['source_path']}"])
blob = subprocess.check_output([
    "git", "rev-parse", f"{FREEZE['source_commit']}:{FREEZE['source_path']}"],
    text=True).strip()
old = (b"result = dict(event='input_admission', key=key, admitted_ns=admitted,\r\n"
      b"                                          input_ack_ns=time.perf_counter_ns(), valid_until_ns=lease.deadline)")
new = (b"result = dict(event='input_admission', key=key, keycode=code, admitted_ns=admitted,\r\n"
      b"                                          input_ack_ns=time.perf_counter_ns(), valid_until_ns=lease.deadline)")
candidate = source.replace(old, new, 1)
arms = RESULT["arms"]
checks = {
    "pinned_blob": blob == FREEZE["source_blob"],
    "raw_source_hash": sha(source) == FREEZE["source_raw_sha256"],
    "unique_candidate_mutation": source.count(old) == 1,
    "candidate_hash": sha(candidate) == FREEZE["candidate_source_sha256"] == RESULT["source_sha256"],
    "probe_hash": sha((ROOT / "probe.py").read_bytes()) == FREEZE["probe_sha256"],
    "audit_script_hash": sha((ROOT / "audit.py").read_bytes()) == FREEZE["audit_sha256"],
    "result_hash": sha((ROOT / "RESULT.json").read_bytes()) == FREEZE["result_sha256"],
    "post_admission_remap_join": (
        arms[0]["admission_keycodes"] == [87, 65] and
        arms[0]["release_keycodes"] == [87, 65] and
        arms[0]["verified"] is True and arms[0]["reason"] == "cancelled"),
    "inter_admission_remap_join": (
        arms[1]["admission_keycodes"] == [87, 77] and
        arms[1]["release_keycodes"] == [87, 77] and
        arms[1]["verified"] is True and arms[1]["reason"] == "cancelled"),
}
output = {"schema": "cancel-key-release-keymap-epoch-audit-v1",
          "checks": checks, "pass": all(checks.values())}
print(json.dumps(output, indent=2, sort_keys=True))
if not output["pass"]:
    raise SystemExit(1)
