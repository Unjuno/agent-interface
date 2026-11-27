import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
source_manifest = json.loads((ROOT / "source_hashes.json").read_text(encoding="utf-8"))
stdout = (ROOT / "results/wslc.stdout.txt").read_text(encoding="utf-8-sig")
exit_code = int((ROOT / "results/exit.txt").read_text(encoding="utf-8").strip())
receipt = json.loads((ROOT / "results/feedback_receipt.json").read_text(encoding="utf-8"))

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
test_ok = hashlib.sha256((ROOT / "test_a12_soft_feedback_turn.py").read_bytes()).hexdigest() == freeze["test_sha256"]
container_ok = hashlib.sha256((ROOT / "Containerfile").read_bytes()).hexdigest() == freeze["containerfile_sha256"]
raw = re.search(r"A12_RESULT=(\{[^\r\n]+\})", stdout)
raw_result = json.loads(raw.group(1)) if raw else None
names = re.findall(r"^(test_[a-z0-9_]+) \(test_a12_soft_feedback_turn\.[^)]+\) \.\.\. ok$", stdout, re.M)
transcript_ok = (exit_code == 0 and len(names) == 2 and "Ran 2 tests in " in stdout and
                 re.search(r"^OK$", stdout, re.M) is not None and raw_result == receipt)
behavior_ok = (
    receipt["cover_admission_status"] == "admitted" and
    receipt["cover_hard_ammo_floor"] == 1 and not receipt["cover_invalidated"] and
    receipt["summary"]["source_value"] == 6 and receipt["summary"]["current_value"] == 4 and
    receipt["summary"]["effect"] == "prior_cover_preserved" and
    receipt["summary"]["grants_input_authority"] is False and
    receipt["prompt_has_current_ammo"] and receipt["prompt_has_summary"] and
    receipt["summary_grants_input_authority"] is False)
sources_ok = all(all(row[k] for k in ("git_blob_matches", "sha256_matches", "bytes_match"))
                 for row in source_checks)
passed = sources_ok and test_ok and container_ok and transcript_ok and behavior_ok
result = {
    "audit_status": "PASS_SCOPED" if passed else "HOLD_AUDIT_MISMATCH",
    "audit_method": "Non-executing source identity, WSLc transcript, and receipt audit; test not rerun.",
    "main_commit": freeze["main_commit"],
    "source_checks": source_checks,
    "test_hash_matches": test_ok,
    "containerfile_hash_matches": container_ok,
    "transcript_exit_zero_and_receipt_matches": transcript_ok,
    "feedback_delivery_invariants_match": behavior_ok,
    "limits": ["recording fake planner client", "no model response or use of feedback", "no live game/input/release"]
}
(ROOT / "results/audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if passed else 1)
