import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
source_manifest = json.loads((ROOT / "source_hashes.json").read_text(encoding="utf-8"))
stdout = (ROOT / "results/wslc.stdout.txt").read_text(encoding="utf-8-sig")
exit_code = int((ROOT / "results/exit.txt").read_text(encoding="utf-8").strip())
gap = json.loads((ROOT / "results/positive_ammo_gap.json").read_text(encoding="utf-8"))
zero = json.loads((ROOT / "results/zero_ammo.json").read_text(encoding="utf-8"))

source_checks = []
for name, expected in freeze["sources"].items():
    data = (ROOT / name).read_bytes()
    oid = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    source_checks.append({
        "source": name,
        "git_blob_matches": oid == expected["git_blob"] == source_manifest[name]["git_blob"],
        "sha256_matches": hashlib.sha256(data).hexdigest() == expected["sha256"] == source_manifest[name]["sha256"],
        "bytes_match": len(data) == expected["bytes"] == source_manifest[name]["bytes"],
    })

test_ok = hashlib.sha256((ROOT / "test_a11_ammo_propagation.py").read_bytes()).hexdigest() == freeze["test_sha256"]
container_ok = hashlib.sha256((ROOT / "Containerfile").read_bytes()).hexdigest() == freeze["containerfile_sha256"]
raw_lines = [json.loads(line.split("=", 1)[1]) for line in stdout.splitlines()
             if line.startswith("A11_RESULT=")]
names = re.findall(r"^(test_[a-z0-9_]+) \(test_a11_ammo_propagation\.[^)]+\) \.\.\. ok$", stdout, re.M)
transcript_ok = (exit_code == 0 and len(names) == 2 and "Ran 2 tests in " in stdout and
                 re.search(r"^OK$", stdout, re.M) is not None and raw_lines == [gap, zero])
behavior_ok = (
    gap["planner_authored_minimum_ammo"] == 5 and gap["current_ammo"] == 4 and
    gap["action_admission_status"] == "REJECTED_PREDICATE" and
    gap["action_admission_reason"] == "ammo_minimum_failed" and
    gap["cover_ammo_hard_minimum"] == 1 and not gap["cover_monitor_invalidated"] and
    zero["current_ammo"] == 0 and zero["monitor_invalidated"] and zero["hard_minimum"] == 1
)
sources_ok = all(all(row[k] for k in ("git_blob_matches", "sha256_matches", "bytes_match"))
                 for row in source_checks)
passed = sources_ok and test_ok and container_ok and transcript_ok and behavior_ok
result = {
    "audit_status": "PASS_SCOPED" if passed else "HOLD_AUDIT_MISMATCH",
    "audit_method": "Non-executing frozen-source, test-transcript, and result audit; tests not rerun.",
    "main_commit": freeze["main_commit"],
    "source_checks": source_checks,
    "test_hash_matches": test_ok,
    "containerfile_hash_matches": container_ok,
    "transcript_exit_zero_and_results_match": transcript_ok,
    "policy_boundary_pattern_matches": behavior_ok,
    "interpretation": "Action minimum_ammo=5 rejects current ammo 4 while cover guard (hard minimum 1) does not invalidate; both contract boundaries are exercised, but intent equivalence is not established.",
    "limits": ["synthetic HUD values", "source-level policy comparison", "no pending-model or live cover cancel", "no physical input/release or task effect"]
}
(ROOT / "results/audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if passed else 1)
