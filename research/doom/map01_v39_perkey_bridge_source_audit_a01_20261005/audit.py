#!/usr/bin/env python3
"""Independent raw/source-only audit of the one-shot attribution result."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PKG = Path(__file__).resolve().parent
OUT = PKG / "results/source-audit-a05"
FILES = {
    "a02_freeze": "research/doom/map01_v39_perkey_bridge_a02_20261005/FREEZE.json",
    "a02_composition": "research/doom/map01_v39_perkey_bridge_a02_20261005/composition.py",
    "a02_trace": "research/doom/map01_v39_perkey_bridge_a02_20261005/results/construction-a02/operation-trace.jsonl",
    "a02_test_owner": "research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12/input_owner_v12.py",
    "a02_adapter": "research/doom/map01_attack_onset_phase_allocation_02_v1/source/map01_v12_transition_owner.py",
    "a02_bridge_harness": "research/doom/map01_v39_perkey_bridge_a01/test_bridge.py",
    "v15_session": "research/doom/session_map01_v15.py",
    "batch_backend": "research/doom/doom_owner_thread_release_batch_backend_v1.py",
    "v4_owner": "research/live_control/input_transition_owner_v4.py",
    "v3_owner": "research/live_control/input_transition_owner_v3.py",
    "production_owner": "research/live_control/input_owner_v12.py",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def function_nodes(source: str, name: str):
    return [node for node in ast.walk(ast.parse(source))
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]


def main() -> int:
    candidate = json.loads((OUT / "candidate.json").read_text(encoding="utf-8"))
    errors = []
    for key, path in FILES.items():
        expected = candidate.get("source_sha256", {}).get(path)
        actual = sha((ROOT / path).read_bytes())
        if expected != actual:
            errors.append("source_hash:" + key)

    freeze = json.loads((ROOT / FILES["a02_freeze"]).read_bytes())
    comp = (ROOT / FILES["a02_composition"]).read_text(encoding="utf-8")
    bridge_harness = (ROOT / FILES["a02_bridge_harness"]).read_text(encoding="utf-8")
    a02_owner = (ROOT / FILES["a02_test_owner"]).read_text(encoding="utf-8")
    v15 = (ROOT / FILES["v15_session"]).read_text(encoding="utf-8")
    v4 = (ROOT / FILES["v4_owner"]).read_text(encoding="utf-8")
    v3 = (ROOT / FILES["v3_owner"]).read_text(encoding="utf-8")
    owner = (ROOT / FILES["production_owner"]).read_text(encoding="utf-8")
    trace = [json.loads(line) for line in (ROOT / FILES["a02_trace"]).read_text().splitlines()]
    between = [row for row in json.loads((OUT / "trace-between-edges.json").read_text())]
    ups = [i for i, row in enumerate(trace) if row.get("operation") == "key-up"]
    if len(ups) != 2:
        errors.append("trace_up_count")
        expected_between = []
    else:
        expected_between = trace[ups[0] + 1:ups[1]]
    if between != expected_between:
        errors.append("trace_slice_mismatch")
    if [r.get("operation") for r in between].count("keymap-sample") != 2:
        errors.append("trace_interrelease_sample_count")

    if "map01_attack_onset_phase_allocation_02_v1" not in comp:
        errors.append("a02_dependency_path_missing")
    if not ("load_v12_test_harness" in bridge_harness
            and "V12 / \"input_owner_v12.py\"" in bridge_harness):
        errors.append("a02_harness_does_not_resolve_historical_v12_owner")
    if "input_transition_owner_v4.py" in freeze.get("source_sha256", {}):
        errors.append("a02_freeze_claims_production_v4")
    if "session_map01_v15.py" in freeze.get("source_sha256", {}):
        errors.append("a02_freeze_claims_v15")
    for needed in ("doom_owner_thread_release_batch_backend_v1.py",
                   "input_transition_owner_v4.py", "live_control/input_owner_v12.py"):
        if needed not in v15:
            errors.append("v15_closure_missing:" + needed)
    if "from input_owner_v12 import InputOwner as OwnerWithKeyUpReceipt" not in v4:
        errors.append("v4_owner_target_missing")
    if "from input_transition_owner_v3 import InputOwner as Previous" not in v4:
        errors.append("v4_previous_missing")
    if "query_keymap" in v4 or "query_keymap" in v3:
        errors.append("production_transition_adapter_queries_keymap")
    a02_run = function_nodes(a02_owner, "_run")
    a02_sample = function_nodes(a02_owner, "sample_key_state")
    if len(a02_run) != 1 or len(a02_sample) != 1:
        errors.append("a02_historical_owner_helper_shape")
    else:
        run_text = ast.get_source_segment(a02_owner, a02_run[0])
        sample_text = ast.get_source_segment(a02_owner, a02_sample[0])
        explicit_up_text = run_text[run_text.index("owner_owned = code in held"):]
        if not (
            "bitmap=d.query_keymap()" in sample_text
            and "pre = sample_key_state(code)" in explicit_up_text
            and "xtest.fake_input(d, X.KeyRelease, code)" in explicit_up_text
            and "post = sample_key_state(code)" in explicit_up_text
            and explicit_up_text.index("pre = sample_key_state(code)")
            < explicit_up_text.index("xtest.fake_input(d, X.KeyRelease, code)")
            < explicit_up_text.index("post = sample_key_state(code)")
        ):
            errors.append("a02_historical_up_probe_order")
    owner_tree = ast.parse(owner)
    query_nodes = [node for node in ast.walk(owner_tree)
                   if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                   and node.func.attr == "query_keymap"]
    release_nodes = [node for node in ast.walk(owner_tree)
                     if isinstance(node, ast.FunctionDef) and node.name == "release"]
    if len(query_nodes) != 1 or len(release_nodes) != 1:
        errors.append("production_query_keymap_not_unique_release_helper")
    elif query_nodes[0] not in ast.walk(release_nodes[0]):
        errors.append("production_query_keymap_outside_terminal_release_helper")
    if "self.owner.call(\"input_state\")" not in (ROOT / FILES["batch_backend"]).read_text():
        errors.append("postbatch_owner_sample_missing")
    if candidate.get("status") != "PASS_ATTRIBUTION_ONLY":
        errors.append("candidate_not_pass")
    if not all(candidate.get("assertions", {}).values()):
        errors.append("candidate_assertion_false")

    audit = {
        "schema": "map01-v39-perkey-source-attribution-audit-v1",
        "run_id": candidate.get("run_id"),
        "status": "PASS_ATTRIBUTION_ONLY" if not errors else "FAIL_SOURCE_ATTRIBUTION_AUDIT",
        "errors": errors,
        "candidate_sha256": sha((OUT / "candidate.json").read_bytes()),
        "runner_sha256": candidate.get("runner_sha256"),
        "trace_slice_sha256": sha((OUT / "trace-between-edges.json").read_bytes()),
        "recomputed": {
            "trace_rows": len(trace),
            "key_up_edges": len(ups),
            "interrelease_keymap_samples": sum(
                row.get("operation") == "keymap-sample" for row in between),
            "production_query_keymap_sites": len(query_nodes),
        },
        "scope": "independent recomputation from frozen raw trace and source files; no runtime or live-effect claim",
    }
    (OUT / "audit-v2.json").write_text(
        json.dumps(audit, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": audit["status"], "errors": len(errors)}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
