#!/usr/bin/env python3
"""One-shot, read-only attribution audit of the retained A02 trace."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PKG = Path(__file__).resolve().parent
OUT = PKG / "results/source-audit-a05"
BASE = "69dd261430cb1ed875f5a76411c4a2a54777c114"

FILES = {
    "a02_freeze": "research/doom/map01_v39_perkey_bridge_a02_20261005/FREEZE.json",
    "a02_composition": "research/doom/map01_v39_perkey_bridge_a02_20261005/composition.py",
    "a02_trace": "research/doom/map01_v39_perkey_bridge_a02_20261005/results/construction-a02/operation-trace.jsonl",
    "a02_test_owner": "research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12/input_owner_v12.py",
    "a02_adapter": "research/doom/map01_attack_onset_phase_allocation_02_v1/source/map01_v12_transition_owner.py",
    "a02_bridge_harness": "research/doom/map01_v39_perkey_bridge_a01/test_bridge.py",
    "v15_session": "research/doom/session_map01_v15.py",
    "batch_backend": "research/doom/doom_owner_thread_release_batch_backend_v1.py",
    "v4_backend": "research/doom/doom_retained_input_backend_v4.py",
    "v4_fixture": "research/doom/test_doom_retained_input_backend_v4.py",
    "v4_owner": "research/live_control/input_transition_owner_v4.py",
    "v3_owner": "research/live_control/input_transition_owner_v3.py",
    "production_owner": "research/live_control/input_owner_v12.py",
}


def read(key: str) -> bytes:
    return (ROOT / FILES[key]).read_bytes()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def function_node(source: bytes, name: str) -> ast.FunctionDef:
    tree = ast.parse(source.decode("utf-8"))
    return next(node for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == name)


def call_names(node: ast.AST) -> list[str]:
    return [item.func.attr if isinstance(item.func, ast.Attribute)
            else item.func.id if isinstance(item.func, ast.Name) else ""
            for item in ast.walk(node) if isinstance(item, ast.Call)]


def main() -> int:
    if OUT.exists():
        raise SystemExit("refusing to replace existing source-audit output")
    if not (ROOT / ".git").exists():
        raise SystemExit("repository root unavailable")

    freeze = json.loads(read("a02_freeze"))
    composition = read("a02_composition").decode("utf-8")
    v15 = read("v15_session").decode("utf-8")
    v4 = read("v4_owner").decode("utf-8")
    v3 = read("v3_owner")
    prod_owner = read("production_owner")
    a02_owner = read("a02_test_owner")
    a02_adapter = read("a02_adapter").decode("utf-8")
    bridge_harness = read("a02_bridge_harness").decode("utf-8")
    batch = read("batch_backend").decode("utf-8")
    trace = [json.loads(line) for line in read("a02_trace").decode().splitlines()]

    key_up_indices = [i for i, row in enumerate(trace) if row["operation"] == "key-up"]
    if len(key_up_indices) != 2:
        raise SystemExit("A02 retained trace does not have exactly two key-up injections")
    between = trace[key_up_indices[0] + 1:key_up_indices[1]]
    between_samples = [row for row in between if row["operation"] == "keymap-sample"]

    a02_source_pins = set(freeze["source_sha256"])
    a02_uses_fixture = (
        "map01_attack_onset_phase_allocation_02_v1" in composition
        and "load_v12_test_harness" in composition
        and "map01_v12_transition_owner.py" in composition
        and "load_v12_test_harness" in bridge_harness
        and "V12 / \"input_owner_v12.py\"" in bridge_harness
        and "input_transition_owner_v4.py" not in a02_source_pins
        and "session_map01_v15.py" not in a02_source_pins
    )
    production_selected = (
        "doom_owner_thread_release_batch_backend_v1.py" in v15
        and "input_transition_owner_v4.py" in v15
        and "live_control/input_owner_v12.py" in v15
        and "from input_owner_v12 import InputOwner as OwnerWithKeyUpReceipt" in v4
        and "from input_transition_owner_v3 import InputOwner as Previous" in v4
    )
    explicit_up = function_node(prod_owner, "_run")
    explicit_up_text = ast.get_source_segment(prod_owner.decode("utf-8"), explicit_up)
    a02_up_text = ast.get_source_segment(a02_owner.decode("utf-8"),
                                         function_node(a02_owner, "_run"))
    a02_sample = ast.get_source_segment(a02_owner.decode("utf-8"),
                                        function_node(a02_owner, "sample_key_state"))
    v4_up = function_node(v4.encode("utf-8"), "call")
    v3_up = function_node(v3, "call")
    owner_tree = ast.parse(prod_owner.decode("utf-8"))
    production_keymap_sites = [
        node
        for node in ast.walk(owner_tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr == "query_keymap"
    ]
    release_functions = [node for node in ast.walk(owner_tree)
                         if isinstance(node, ast.FunctionDef) and node.name == "release"]
    assertions = {
        "trace_has_two_up_edges": len(key_up_indices) == 2,
        "trace_has_two_keymap_samples_between_up_edges": len(between_samples) == 2,
        "a02_uses_injected_historical_v12_harness": a02_uses_fixture,
        "a02_freeze_omits_v39_v15_and_v4_source": (
            "input_transition_owner_v4.py" not in a02_source_pins
            and "session_map01_v15.py" not in a02_source_pins
        ),
        "v15_selects_v39_release_batch_and_v4": production_selected,
        "production_v4_call_does_not_query_keymap": "query_keymap" not in ast.get_source_segment(v4, v4_up),
        "production_v3_call_does_not_query_keymap": "query_keymap" not in ast.get_source_segment(v3.decode("utf-8"), v3_up),
        "production_up_uses_keyrelease_and_sync": (
            "KeyRelease" in explicit_up_text and "d.sync()" in explicit_up_text
        ),
        "production_keymap_query_is_terminal_release_cleanup": (
            len(production_keymap_sites) == 1
            and len(release_functions) == 1
            and production_keymap_sites[0] in ast.walk(release_functions[0])
            and "bitmap = d.query_keymap()" in prod_owner.decode("utf-8")
        ),
        "production_batch_samples_owner_after_explicit_up": (
            "self.owner.call(\"input_state\")" in batch
            and "all explicit key-up calls in this backend-held batch complete before " in batch
        ),
        "a02_adapter_is_only_a_transition_wrapper": (
            "self._inner.call(operation,lease,key)" in a02_adapter
            and "input_release_measurement" in a02_adapter
        ),
        "a02_historical_owner_samples_around_each_explicit_up": (
            "bitmap=d.query_keymap()" in a02_sample
            and "pre = sample_key_state(code)" in a02_up_text[a02_up_text.index("owner_owned = code in held"):]
            and "xtest.fake_input(d, X.KeyRelease, code)" in a02_up_text[a02_up_text.index("owner_owned = code in held"):]
            and "post = sample_key_state(code)" in a02_up_text[a02_up_text.index("owner_owned = code in held"):]
            and a02_up_text[a02_up_text.index("owner_owned = code in held"):].index("pre = sample_key_state(code)")
            < a02_up_text[a02_up_text.index("owner_owned = code in held"):].index("xtest.fake_input(d, X.KeyRelease, code)")
            < a02_up_text[a02_up_text.index("owner_owned = code in held"):].index("post = sample_key_state(code)")
        ),
    }
    status = "PASS_ATTRIBUTION_ONLY" if all(assertions.values()) else "FAIL_SOURCE_ATTRIBUTION"
    OUT.mkdir(parents=True)
    (OUT / "trace-between-edges.json").write_text(
        json.dumps(between, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    result = {
        "schema": "map01-v39-perkey-source-attribution-candidate-v1",
        "run_id": "MAP01-V39-PERKEY-SOURCE-ATTRIBUTION-A05-20261005",
        "base_commit": BASE,
        "status": status,
        "assertions": assertions,
        "counts": {
            "a02_trace_rows": len(trace),
            "key_up_edges": len(key_up_indices),
            "keymap_samples_between_up_edges": len(between_samples),
            "production_keymap_query_sites": len(production_keymap_sites),
        },
        "source_sha256": {FILES[key]: sha(read(key)) for key in sorted(FILES)},
        "runner_sha256": sha(Path(__file__).read_bytes()),
        "interpretation": (
            "The retained A02 between-key samples are the historical V12 owner's per-key "
            "physical-edge probes: the first up's post-sample and the next up's pre-sample. "
            "The injected transition wrapper only joins that receipt. They do not demonstrate "
            "an inter-release query in the V39 "
            "V15 production closure. Production V39 explicit-up receipts are XTest/XSync only; "
            "physical keymap is sampled at terminal cleanup, and one owner-state sample follows "
            "the ordinary release batch."
        ),
        "scope": (
            "read-only source and retained-trace attribution; no candidate rerun, no live X11, "
            "GUI, OS input, game, model, application effect, threat response, recovery, or latency bound"
        ),
    }
    (OUT / "candidate.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "assertions_passed": sum(assertions.values()),
                      "assertions_total": len(assertions)}, sort_keys=True))
    return 0 if status == "PASS_ATTRIBUTION_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
