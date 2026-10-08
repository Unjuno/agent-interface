"""Audit fake sink outcomes and exact source control-flow boundary."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "executor_v13.py"


def audit():
    raw = json.loads((ROOT / "raw.json").read_text(encoding="utf-8"))
    pins = json.loads((ROOT / "source-pins.json").read_text(encoding="utf-8"))
    source_bytes = SOURCE.read_bytes()
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    executor = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Executor")
    run = next(n for n in executor.body if isinstance(n, ast.FunctionDef) and n.name == "_run")
    finally_body = next((n.finalbody for n in ast.walk(run)
                         if isinstance(n, ast.Try) and n.finalbody), [])
    publish_index = next((i for i, n in enumerate(finally_body)
                          if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and
                          isinstance(n.value.func, ast.Attribute) and n.value.func.attr == "_publish_cause_once"), None)
    release_index = next((i for i, n in enumerate(finally_body)
                          if any(isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and
                                 call.func.attr == "release_all" for call in ast.walk(n))), None)
    finally_publish_precedes_release = (publish_index is not None and release_index is not None and
                                        publish_index < release_index)
    errors = []
    if raw.get("schema") != "v39-release-sink-failure-t0-raw-v1":
        errors.append("schema")
    if raw.get("source_git_blob") != "7f308a0dd863af534f764f657d603b4921ba1c6a":
        errors.append("source_blob")
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    git_blob = hashlib.sha1(b"blob " + str(len(source_bytes)).encode() + b"\0" + source_bytes).hexdigest()
    if raw.get("source_sha256") != source_sha256:
        errors.append("source_sha256")
    if (pins.get("pr_7474_head") != "3e498aebd77e500d5a7b1ac9d434d37350a9f597" or
            pins.get("pr_7474_source_git_blob") != git_blob or
            pins.get("source_sha256") != source_sha256):
        errors.append("source_pins")
    cases = {row.get("sink_mode"): row for row in raw.get("rows", [])}
    if set(cases) != {"success", "fail_before_accept", "accept_then_raise"}:
        errors.append("case_set")
    success = cases.get("success", {})
    if (len(success.get("accepted_events", [])) != 1 or
            success.get("accepted_events", [{}])[0].get("event") != "input_released" or
            not success.get("published_release_marked") or not success.get("retry_suppressed")):
        errors.append("success_control")
    before = cases.get("fail_before_accept", {})
    if (before.get("accepted_events") or not before.get("published_release_marked") or
            not before.get("retry_suppressed") or before.get("delivery_unknown_events")):
        errors.append("fail_before_accept")
    after = cases.get("accept_then_raise", {})
    if (len(after.get("accepted_events", [])) != 1 or
            after.get("accepted_events", [{}])[0].get("event") != "input_released" or
            not after.get("published_release_marked") or not after.get("retry_suppressed") or
            after.get("delivery_unknown_events")):
        errors.append("accept_then_raise")
    if not finally_publish_precedes_release:
        errors.append("run_finally_publication_order")
    return {
        "schema": "v39-release-sink-failure-t0-audit-v1",
        "pass": not errors,
        "errors": errors,
        "classification": "SINK_FAILURE_MARKED_PUBLISHED_RETRY_SUPPRESSED_WITHOUT_UNKNOWN_CUSTODY" if not errors else "AUDIT_FAIL",
        "finally_publish_precedes_release_all": finally_publish_precedes_release,
        "scope": "exact helper methods and static caller structure with fake sinks only",
    }


if __name__ == "__main__":
    result = audit()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (ROOT / "audit.json").write_text(text, encoding="utf-8")
    print(text, end="")
    raise SystemExit(0 if result["pass"] else 1)
