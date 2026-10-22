"""Independently adjudicate the frozen candidate JSON without importing it."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
FREEZE = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))
RAW = json.loads((PACKAGE / "results/pending-loop-a01/candidate.raw.json").read_text(encoding="utf-8"))
EXPECTED_CANCEL = ["model_pending", "hud_invalidation_observed_while_pending",
                   "planner_interrupt_requested", "cover_cancel_emitted",
                   "verified_empty_release", "late_model_answer_returned"]
errors = []
for name, digest in FREEZE["implementation_file_sha256"].items():
    if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
        errors.append("source hash mismatch: " + name)
for name, digest in FREEZE["study_scripts_sha256"].items():
    if hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest() != digest:
        errors.append("study script hash mismatch: " + name)
if RAW.get("repository_commit") != FREEZE["repository_commit"]:
    errors.append("repository commit mismatch")
if RAW.get("implementation_file_sha256") != FREEZE["implementation_file_sha256"]:
    errors.append("raw source hashes mismatch")
if RAW.get("status") != "PASS_CONSTRUCTION_SCOPED":
    errors.append("candidate did not report construction pass")
cases = {row.get("case"): row for row in RAW.get("cases", [])}
if set(cases) != {"hard_health", "unknown_pair_binding", "soft_change"}:
    errors.append("case set mismatch")
for case in ("hard_health", "unknown_pair_binding"):
    row = cases.get(case, {})
    if row.get("events") != EXPECTED_CANCEL:
        errors.append(case + " cancellation order mismatch")
    if row.get("final_admission", {}).get("status") != "REJECTED_POLICY_INVALIDATED":
        errors.append(case + " returned answer not rejected")
    if row.get("final_admission", {}).get("input_authority_admitted") is not False:
        errors.append(case + " granted input authority")
    receipts = row.get("terminal_receipts", [])
    if (len(receipts) != 1 or receipts[0].get("status") != "cancelled" or
            receipts[0].get("release") != {"verified": True, "keys_down": [], "buttons_down": []}):
        errors.append(case + " empty release receipt mismatch")
if cases.get("hard_health", {}).get("invalidation", {}).get("outcomes", {}).get("health", {}).get("status") != "HARD_INVALIDATED":
    errors.append("health crossing was not hard-invalidated")
if cases.get("unknown_pair_binding", {}).get("invalidation", {}).get("outcome", {}).get("status") != "UNKNOWN":
    errors.append("pair binding mismatch was not unknown")
soft = cases.get("soft_change", {})
if soft.get("events") != ["model_pending", "soft_change_preserved_while_pending", "late_model_answer_returned"]:
    errors.append("soft change was interrupted")
if soft.get("final_admission", {}).get("status") != "READY_FOR_ACTION_VALIDITY":
    errors.append("soft change skipped fresh action validity")
if soft.get("cancel_commands") != [] or soft.get("planner_interrupt_calls") != 0:
    errors.append("soft change emitted cancellation")
result = {"schema": "v39-pending-model-invalidation-a01-audit-v1",
          "status": "PASS_SNAPSHOT_AND_REPLAY_AUDIT" if not errors else "FAIL_AUDIT",
          "errors": errors, "cases_checked": len(cases),
          "python": sys.version.split()[0], "live_allocation": False}
print(json.dumps(result, sort_keys=True, separators=(",", ":")))
raise SystemExit(0 if not errors else 1)
