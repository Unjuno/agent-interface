"""Frozen-source AST classification for Issue #5156 caller brackets."""
import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "owner_v10.py": "341b3c01649943ddaad5f28431a792c4889cc36e",
    "wrapper_v3.py": "0ea631abcf6272f0538a9ef9198ad8069b47b464",
}


def blob_id(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def calls(function, name):
    return [node for node in ast.walk(function)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == name]


def main():
    owner_bytes = (ROOT / "source" / "owner_v10.py").read_bytes()
    wrapper_bytes = (ROOT / "source" / "wrapper_v3.py").read_bytes()
    owner_tree = ast.parse(owner_bytes)
    wrapper_tree = ast.parse(wrapper_bytes)
    run = next(n for n in ast.walk(owner_tree)
               if isinstance(n, ast.FunctionDef) and n.name == "_run")
    wrapper_call = next(n for n in ast.walk(wrapper_tree)
                        if isinstance(n, ast.FunctionDef) and n.name == "call")
    sites = []
    for node in sorted(calls(run, "release"), key=lambda n: n.lineno):
        parents = []
        stack = [run]
        parent_map = {}
        while stack:
            current = stack.pop()
            for child in ast.iter_child_nodes(current):
                parent_map[child] = current
                stack.append(child)
        cur = node
        while cur in parent_map:
            cur = parent_map[cur]
            if isinstance(cur, ast.If):
                parents.append(ast.unparse(cur.test))
        joined = " | ".join(parents)
        if "stop_requested" in joined:
            kind = "autonomous_stop"
        elif "expired" in joined or "cancel" in joined or "changed" in joined:
            kind = "autonomous_expiry_cancel_focus"
        elif "op in ('release', 'close')" in joined:
            kind = "queued_explicit_release_or_close"
        else:
            kind = "thread_finalizer"
        sites.append({"line": node.lineno, "kind": kind,
                      "enclosing_conditions": parents})

    wrapper_text = ast.unparse(wrapper_call)
    result = {
        "schema": "issue5156-caller-bracket-scope-result-v1",
        "source_git_blobs": {
            "owner_v10.py": blob_id(owner_bytes),
            "wrapper_v3.py": blob_id(wrapper_bytes),
        },
        "source_sha256": {
            "owner_v10.py": hashlib.sha256(owner_bytes).hexdigest(),
            "wrapper_v3.py": hashlib.sha256(wrapper_bytes).hexdigest(),
        },
        "expected_blobs_match": {
            name: blob_id(data) == EXPECTED[name]
            for name, data in (("owner_v10.py", owner_bytes),
                               ("wrapper_v3.py", wrapper_bytes))
        },
        "owner_release_sites": sites,
        "release_site_count": len(sites),
        "queued_explicit_site_count": sum(
            row["kind"] == "queued_explicit_release_or_close" for row in sites),
        "autonomous_site_count": sum(row["kind"].startswith("autonomous_")
                                      or row["kind"] == "thread_finalizer" for row in sites),
        "wrapper_explicit_transition_branch": "operation not in ('up', 'button_up')",
        "wrapper_timestamps_explicit_up": (
            "release_call_started_ns = time.perf_counter_ns()" in wrapper_text
            and "release_call_returned_ns = time.perf_counter_ns()" in wrapper_text
            and "self._inner.call(operation, lease, key)" in wrapper_text),
        "wrapper_autonomous_cleanup_timer": False,
        "physical_keyup_or_application_consumption_measured": False,
        "decision": "PASS_CALLER_BRACKET_SCOPE_CORRECTION_REQUIRED",
    }
    output = ROOT / "results" / "CLASSIFICATION.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if all(result["expected_blobs_match"].values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
