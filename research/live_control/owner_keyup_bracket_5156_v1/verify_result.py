"""Independent source/result audit using a separate AST traversal."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
freeze = json.loads((HERE / "SOURCE_FREEZE.json").read_text(encoding="utf-8"))
result_bytes = (HERE / "result.json").read_bytes()
result = json.loads(result_bytes)
assert result["main_sha"] == freeze["main_sha"]
assert result["disposition"] == "PASS_AUTOMATIC_RELEASE_OUTSIDE_CALLER_BRACKET"
assert result["scope"] == "frozen source control flow only; no owner execution or X11 timing"

blobs = {}
for item in freeze["sources"]:
    data = subprocess.check_output(
        ["git", "cat-file", "blob", f"{freeze['main_sha']}:{item['path']}"], cwd=ROOT
    )
    assert len(data) == item["bytes"]
    assert hashlib.sha256(data).hexdigest() == item["sha256"]
    assert subprocess.check_output(
        ["git", "rev-parse", f"{freeze['main_sha']}:{item['path']}"], cwd=ROOT, text=True
    ).strip() == item["git_blob"]
    blobs[item["path"]] = ast.parse(data.decode("utf-8"), filename=item["path"])


def selected_function(tree: ast.Module, owner: str, name: str) -> ast.FunctionDef:
    return next(
        child for node in tree.body if isinstance(node, ast.ClassDef) and node.name == owner
        for child in node.body if isinstance(child, ast.FunctionDef) and child.name == name
    )


owner = blobs["research/live_control/input_owner_v10.py"]
wrapper = blobs["research/live_control/input_transition_owner_v3.py"]
run_fn = selected_function(owner, "InputOwner", "_run")
call_fn = selected_function(owner, "InputOwner", "call")
wrapper_fn = selected_function(wrapper, "InputOwner", "call")

# Independent call-site walk: identify release() invocations directly inside
# _run and prove client call() is a queue boundary, not the callee of those sites.
local_release_lines = sorted(
    node.lineno for node in ast.walk(run_fn)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "release"
)
assert local_release_lines == [205, 219, 261, 356], local_release_lines
call_names = [
    node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
    for node in ast.walk(call_fn) if isinstance(node, ast.Call)
]
assert "put" in call_names and "wait" in call_names
assert "release" not in call_names, call_names
wrapper_calls = [
    node for node in ast.walk(wrapper_fn) if isinstance(node, ast.Call)
    and isinstance(node.func, ast.Attribute) and node.func.attr == "perf_counter_ns"
]
assert len(wrapper_calls) == 4
assert result["release_callsites"] == [
    {"line": 205, "reason": "'stop_requested'", "context": "owner_loop_stop_flag"},
    {"line": 219, "reason": "'expired' if expired else 'surface_changed' if surface_changed else 'focus_changed' if changed else 'cancelled'", "context": "owner_loop_expiry_cancel_focus"},
    {"line": 261, "reason": "op", "context": "queued_owner_operation"},
    {"line": 356, "reason": "'thread_exit'", "context": "owner_thread_finalizer"},
]
assert result["autonomous_release_callsites"] == [205, 219]
assert result["queued_release_callsites"] == [261]
assert result["finalizer_release_callsites"] == [356]
assert len(result["checks"]) == 9 and all(result["checks"].values())

def accepts_summary(value: dict) -> bool:
    return (
        value.get("schema") == "owner-keyup-caller-boundary-result-v1"
        and value.get("main_sha") == freeze["main_sha"]
        and value.get("disposition") == "PASS_AUTOMATIC_RELEASE_OUTSIDE_CALLER_BRACKET"
        and value.get("autonomous_release_callsites") == [205, 219]
        and value.get("queued_release_callsites") == [261]
        and value.get("finalizer_release_callsites") == [356]
        and [row.get("line") for row in value.get("release_callsites", [])] == [205, 219, 261, 356]
        and all(value.get("checks", {}).values())
        and value.get("source_blobs") == {item["path"]: item["git_blob"] for item in freeze["sources"]}
    )


mutations = {
    "wrong_disposition": lambda x: x.update(disposition="PASS_CALLER_BRACKET_ALWAYS_PRESENT"),
    "wrong_main_sha": lambda x: x.update(main_sha="0" * 40),
    "missing_cancel_expiry_site": lambda x: x.update(autonomous_release_callsites=[205]),
    "wrong_source_blob": lambda x: x["source_blobs"].update({"research/live_control/input_owner_v10.py": "0" * 40}),
    "failed_source_check": lambda x: x["checks"].update(client_call_enqueues_and_waits=False),
    "wrong_callsite": lambda x: x["release_callsites"].pop(),
}
controls = []
for name, mutate in mutations.items():
    damaged = copy.deepcopy(result)
    mutate(damaged)
    controls.append({"name": name, "rejected": not accepts_summary(damaged)})
assert all(row["rejected"] for row in controls), controls

audit = {
    "schema": "owner-keyup-caller-boundary-audit-v1",
    "status": "PASS",
    "result_sha256": hashlib.sha256(result_bytes).hexdigest(),
    "source_count": len(blobs),
    "release_callsites": len(local_release_lines),
    "autonomous_release_callsites": [205, 219],
    "queued_release_callsites": [261],
    "conditional_finalizer_release_callsites": [356],
    "mutation_controls": controls,
    "errors": [],
}
(HERE / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"independent_verification": "PASS", "sources": len(blobs),
                  "callsites": len(local_release_lines), "autonomous": 2,
                  "queued": 1, "conditional_finalizer": 1,
                  "corruption_controls_rejected": len(controls),
                  "result_sha256": audit["result_sha256"]}, sort_keys=True))
