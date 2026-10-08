"""Frozen-source caller-boundary analysis; never imports or runs the owner."""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FREEZE = json.loads((HERE / "SOURCE_FREEZE.json").read_text(encoding="utf-8"))


def source(path: str) -> bytes:
    return subprocess.check_output(
        ["git", "cat-file", "blob", f"{FREEZE['main_sha']}:{path}"], cwd=ROOT
    )


def method(tree: ast.AST, class_name: str, method_name: str) -> ast.FunctionDef:
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == class_name]
    assert len(classes) == 1, (class_name, len(classes))
    methods = [n for n in classes[0].body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == method_name]
    assert len(methods) == 1, (class_name, method_name, len(methods))
    return methods[0]


def names(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def main() -> None:
    sources = {}
    for row in FREEZE["sources"]:
        data = source(row["path"])
        assert len(data) == row["bytes"]
        assert hashlib.sha256(data).hexdigest() == row["sha256"]
        blob = subprocess.check_output(
            ["git", "rev-parse", f"{FREEZE['main_sha']}:{row['path']}"], cwd=ROOT, text=True
        ).strip()
        assert blob == row["git_blob"]
        sources[row["path"]] = data.decode("utf-8")

    owner_path = "research/live_control/input_owner_v10.py"
    wrapper_path = "research/live_control/input_transition_owner_v3.py"
    owner_tree = ast.parse(sources[owner_path], filename=owner_path)
    wrapper_tree = ast.parse(sources[wrapper_path], filename=wrapper_path)
    call_method = method(owner_tree, "InputOwner", "call")
    run_method = method(owner_tree, "InputOwner", "_run")
    wrapper_call = method(wrapper_tree, "InputOwner", "call")

    release_calls = []
    for node in ast.walk(run_method):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "release":
            continue
        arg = ast.unparse(node.args[0]) if node.args else "<no reason>"
        context = {
            "'stop_requested'": "owner_loop_stop_flag",
            "'expired' if expired else 'surface_changed' if surface_changed else 'focus_changed' if changed else 'cancelled'": "owner_loop_expiry_cancel_focus",
            "op": "queued_owner_operation",
            "'thread_exit'": "owner_thread_finalizer",
        }.get(arg, "unclassified")
        release_calls.append({"line": node.lineno, "reason": arg, "context": context})
    release_calls.sort(key=lambda row: row["line"])

    call_text = ast.unparse(call_method)
    run_text = ast.unparse(run_method)
    wrapper_text = ast.unparse(wrapper_call)
    checks = {
        "client_call_enqueues_and_waits": "self.requests.put" in call_text and "done.wait" in call_text,
        "client_call_does_not_invoke_local_release": not any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "release"
            for n in ast.walk(call_method)
        ),
        "autonomous_stop_path_calls_local_release": "release('stop_requested')" in run_text,
        "autonomous_expiry_cancel_focus_path_calls_local_release": any(
            {"expired", "surface_changed", "changed"}.issubset(names(node.args[0]))
            for node in ast.walk(run_method)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "release" and node.args
        ),
        "queued_release_close_path_calls_local_release": "release(op)" in run_text,
        "thread_exit_cleanup_calls_local_release": "release('thread_exit')" in run_text,
        "v3_timestamps_client_up_and_button_up": "operation not in ('up', 'button_up')" in wrapper_text,
        "v3_timestamps_client_release_and_close_only": "operation in ('release', 'close')" in wrapper_text,
        "v3_wrapper_has_no_owner_loop_release_hook": "_run" not in wrapper_text and "release(reason)" not in wrapper_text,
    }
    assert len(release_calls) == 4, release_calls
    assert all(checks.values()), [name for name, ok in checks.items() if not ok]

    autonomous = [row for row in release_calls if row["context"] in {
        "owner_loop_stop_flag", "owner_loop_expiry_cancel_focus"
    }]
    queued = [row for row in release_calls if row["reason"] == "op"]
    finalizer = [row for row in release_calls if row["context"] == "owner_thread_finalizer"]
    assert len(autonomous) == 2 and len(queued) == 1 and len(finalizer) == 1
    result = {
        "schema": "owner-keyup-caller-boundary-result-v1",
        "allocation": FREEZE["allocation"],
        "main_sha": FREEZE["main_sha"],
        "disposition": "PASS_AUTOMATIC_RELEASE_OUTSIDE_CALLER_BRACKET",
        "source_blobs": {row["path"]: row["git_blob"] for row in FREEZE["sources"]},
        "release_callsites": release_calls,
        "autonomous_release_callsites": [row["line"] for row in autonomous],
        "queued_release_callsites": [row["line"] for row in queued],
        "finalizer_release_callsites": [row["line"] for row in finalizer],
        "checks": checks,
        "scope": "frozen source control flow only; no owner execution or X11 timing",
    }
    (HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": result["disposition"], "checks": len(checks),
                      "release_callsites": len(release_calls), "autonomous": len(autonomous),
                      "queued": len(queued), "finalizer": len(finalizer)}, sort_keys=True))


if __name__ == "__main__":
    main()
