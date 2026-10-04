"""Independent checks for the frozen release-all BaseException raw record."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
frozen = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
raw = json.loads((HERE / "raw.json").read_text(encoding="utf-8"))
expected_custody = {
    "schema": "release-batch-delivery-v1",
    "identifier": "cleanup-interrupt",
    "step": 0,
    "size": 1,
    "positions": [{"position": 0, "step": 0, "key": "a", "state": "unknown"}],
}
errors = []
if raw.get("experiment") != frozen.get("experiment"):
    errors.append("experiment identity mismatch")
if raw.get("dependencies_identical") is not True:
    errors.append("baseline and candidate dependencies differ")
base = raw.get("baseline", {})
candidate = raw.get("candidate", {})
if base.get("commit") != frozen["sources"]["baseline_commit"]:
    errors.append("baseline source commit mismatch")
if base.get("executor_source_sha256") != frozen["sources"]["baseline_executor_sha256"]:
    errors.append("baseline executor hash mismatch")
if candidate.get("commit") != frozen["sources"]["candidate_commit"]:
    errors.append("candidate source commit mismatch")
if candidate.get("executor_source_sha256") != frozen["sources"]["candidate_executor_sha256"]:
    errors.append("candidate executor hash mismatch")
if raw.get("dependency_sha256") != frozen["sources"]["dependency_sha256"]:
    errors.append("runtime dependency hash mismatch")
if base.get("terminal_count") != 0 or base.get("active_after_close") is not True:
    errors.append("baseline did not reproduce missing terminal/occupied intent")
if base.get("worker_excepthook") != ["KeyboardInterrupt"]:
    errors.append("baseline worker exception mismatch")
if candidate.get("terminal_count") != 1:
    errors.append("candidate terminal count mismatch")
if candidate.get("terminal_status") != "failed":
    errors.append("candidate terminal status mismatch")
if candidate.get("terminal_error") != "KeyboardInterrupt('release sink interrupted during cleanup')":
    errors.append("candidate terminal error mismatch")
if candidate.get("release", {}).get("verified") is not False:
    errors.append("candidate release did not fail closed")
if candidate.get("release", {}).get("release_batch_delivery") != expected_custody:
    errors.append("candidate terminal custody mismatch")
if candidate.get("worker_excepthook") != ["KeyboardInterrupt"]:
    errors.append("candidate did not propagate the interruption")
if candidate.get("active_after_close") is not False:
    errors.append("candidate left the active intent occupied")
audit = {
    "experiment": frozen["experiment"],
    "result": "PASS_RELEASE_ALL_BASEEXCEPTION_CUSTODY" if not errors else "FAIL",
    "checks": 16,
    "errors": errors,
    "scope": "raw-result consistency only; no physical release or task-effect claim",
}
(HERE / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(audit, indent=2, sort_keys=True))
raise SystemExit(0 if not errors else 1)
