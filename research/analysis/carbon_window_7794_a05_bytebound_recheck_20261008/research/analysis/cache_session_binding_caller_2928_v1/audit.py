"""Independent raw-only reconstruction; imports no caller or probe code."""
import hashlib
import json
import sys
from pathlib import Path

root = Path(__file__).parent
freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8"))
raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
errors = []
if raw.get("schema") != "issue-2928-current-caller-session-binding-raw-v1":
    errors.append("schema")
if raw.get("source_git_blob") != freeze["subject_git_blob"]:
    errors.append("source_git_blob")
if raw.get("source_sha256") != freeze["subject_sha256"]:
    errors.append("source_sha256")
rows = raw.get("rows")
if type(rows) is not list or len(rows) != 2:
    errors.append("row_count")
else:
    for expected, row in zip(freeze["cases"], rows):
        cid = expected["case_id"]
        target = {"target_id": "target-1", "cached_session_id": expected["cached_session_id"]}
        if row.get("case_id") != cid:
            errors.append(cid + ":case_id")
        if row.get("request_session_id") != expected["request_session_id"]:
            errors.append(cid + ":request_session_id")
        if row.get("cached_session_id") != expected["cached_session_id"]:
            errors.append(cid + ":cached_session_id")
        if row.get("reuse_payload") != target or row.get("final_payload") != target:
            errors.append(cid + ":payload")
        if row.get("execute_adapter_calls") != 1:
            errors.append(cid + ":execute_call_count")
        if row.get("completed_actions") != 0 or row.get("effect") is not None:
            errors.append(cid + ":effect_boundary")
        if row.get("outcome") != "EXECUTION_INCOMPLETE":
            errors.append(cid + ":outcome")
result = {
    "schema": "issue-2928-current-caller-session-binding-audit-v1",
    "rows": 0 if type(rows) is not list else len(rows),
    "reconstructed": 0 if type(rows) is not list else len(rows) - len(errors),
    "errors": errors,
    "disposition": "HOLD_SESSION_BINDING_DEPENDS_ON_ADAPTER" if not errors else "STOP_RAW_AUDIT",
    "formal_invocations": 0,
}
rendered = json.dumps(result, sort_keys=True, indent=2) + "\n"
if len(sys.argv) > 2:
    Path(sys.argv[2]).write_text(rendered, encoding="utf-8")
print(rendered, end="")
if errors:
    raise SystemExit(1)
