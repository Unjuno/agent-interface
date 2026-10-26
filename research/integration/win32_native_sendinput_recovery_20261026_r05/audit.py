"""Independent hash and no-input audit for the frozen R05 outcome."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"


def verify_manifest(path, base):
    rows = path.read_text(encoding="utf-8").splitlines()
    failures = []
    for row in rows:
        expected, relative = row.split("  ", 1)
        target = base / relative
        if not target.is_file():
            failures.append({"path": relative, "reason": "missing"})
            continue
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != expected:
            failures.append({"path": relative, "expected": expected, "actual": actual})
    return {"entries": len(rows), "failures": failures}


pretrial = verify_manifest(PACKET / "PRETRIAL_SHA256SUMS", ROOT)
raw = verify_manifest(RUN / "SHA256SUMS", RUN)
result = json.loads((RUN / "result.json").read_text(encoding="utf-8"))
observation = result["public_observation"]
report = observation["receipt"]["source"]["raw_report"]
assert report["status"] == "returned"
assert report["target_generation"] == result["preflight"]["target_generation"]
assert report["input_dispatched"] is False
assert result["close"]["session"]["call_count"] == 0
assert result["close"]["session"]["unresolved_call_ids"] == []
assert result["cleanup"]["fixture_exit_code"] == 0
assert not result["effect_file_present"] if "effect_file_present" in result else not (RUN / "fixture" / "effect.json").exists()

audit = {"attempt_id": result["attempt_id"],
    "classification": result["classification"],
    "pretrial_hash_audit": pretrial, "raw_hash_audit": raw,
    "public_generation_matches_native_preflight": True,
    "input_dispatched": False,
    "action_call_count": result["close"]["session"]["call_count"],
    "unresolved_call_ids": result["close"]["session"]["unresolved_call_ids"],
    "fixture_exit_code": result["cleanup"]["fixture_exit_code"],
    "effect_file_absent": not (RUN / "fixture" / "effect.json").exists(),
    "audit_pass": not pretrial["failures"] and not raw["failures"]}
(PACKET / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
    encoding="utf-8", newline="\n")
print(json.dumps(audit, indent=2, sort_keys=True))
if not audit["audit_pass"]:
    raise SystemExit(1)
