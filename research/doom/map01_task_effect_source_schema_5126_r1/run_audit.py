"""Deterministic host-only static audit of pinned task-effect source schemas."""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
while not (ROOT / ".git").exists() and ROOT != ROOT.parent:
    ROOT = ROOT.parent
FREEZE = json.loads((HERE / "SOURCE_FREEZE.json").read_text(encoding="utf-8"))


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def keys_from_dict(node: ast.AST) -> list[str]:
    if not isinstance(node, ast.Dict):
        raise AssertionError("expected literal dictionary schema")
    keys = []
    for key in node.keys:
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            keys.append(key.value)
        elif isinstance(key, ast.Name):
            keys.append(key.id)
        else:
            keys.append("<dynamic>")
    return keys


def function(path: str, name: str) -> ast.FunctionDef:
    tree = ast.parse(source(path), filename=path)
    found = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    if len(found) != 1:
        raise AssertionError(f"expected one function {name} in {path}, got {len(found)}")
    return found[0]


def dict_return_keys(path: str, name: str) -> list[str]:
    fn = function(path, name)
    returns = [n.value for n in ast.walk(fn) if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict)]
    if len(returns) == 1:
        return keys_from_dict(returns[0])
    if len(returns) > 1:
        raise AssertionError(f"expected at most one literal dict return in {name}, got {len(returns)}")
    calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "dict"]
    if len(calls) != 1:
        raise AssertionError(f"expected one dict(...) schema in {name}, got {len(calls)}")
    return [kw.arg for kw in calls[0].keywords]


def call_dict_keys(path: str, name: str) -> list[str]:
    fn = function(path, name)
    calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "dict"]
    if len(calls) != 1:
        raise AssertionError(f"expected one dict(...) schema in {name}, got {len(calls)}")
    return [kw.arg for kw in calls[0].keywords]


def verify_freeze() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if head != FREEZE["main_sha"]:
        raise AssertionError(f"checkout moved: {head} != frozen {FREEZE['main_sha']}")
    for row in FREEZE["sources"]:
        data = (ROOT / row["path"]).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        blob = subprocess.check_output(["git", "rev-parse", f"HEAD:{row['path']}"], cwd=ROOT, text=True).strip()
        if digest != row["sha256"] or blob != row["git_blob"] or len(data) != row["bytes"]:
            raise AssertionError(f"source freeze mismatch: {row['path']}")


def audit() -> dict:
    verify_freeze()
    v13_release = dict_return_keys("research/live_control/input_transition_owner_v3.py", "call")
    scorer = dict_return_keys("research/doom/independent_progress_clock_v2.py", "_event")
    v12_adapter = call_dict_keys(
        "research/doom/map01_attack_onset_phase_allocation_04_v1/dependencies/v12/input_owner_v12.py",
        "_edge_for_adapter",
    )
    v10 = source("research/live_control/input_owner_v10.py")
    v13 = source("research/doom/session_map01_v13.py")
    backend = source("research/doom/doom_retained_input_backend_v3.py")
    clock = source("research/doom/independent_progress_clock_v2.py")
    scorer_sink = source("research/doom/map01_scorer_stdio_adapter_v1.py")
    legacy_contract = source("research/doom/map01_task_effect_contract_1839_v1/run.py")

    checks = {
        "v13_composes_v12_session_with_v3_backend": "import session_map01_v12 as base" in v13 and "base.Backend=TelemetryBackend" in v13,
        "v13_release_receipt_has_event_name": "input_release_transition" in source("research/live_control/input_transition_owner_v3.py"),
        "v13_release_receipt_declares_no_source_id": "source_event_id" not in source("research/live_control/input_transition_owner_v3.py"),
        "v10_down_admission_declares_no_source_id": "source_event_id" not in v10,
        "v3_backend_emits_release_rows_to_sink": "for receipt in rows:\n            self.emit(receipt)" in backend,
        "scorer_epoch_resets_event_sequence_to_zero": "self._event_sequence = 0" in clock,
        "scorer_event_has_no_epoch_or_source_id": "source_event_id" not in clock and "scorer_epoch_id" not in clock,
        "scorer_sink_writes_independent_jsonl": "scorer-events.jsonl" in scorer_sink,
        "legacy_contract_uses_effect_id_not_producer_source_id": '"effect_id":"e1"' in legacy_contract and 'source_event_id' not in legacy_contract,
    }
    required = [
        "event", "transition_schema", "operation", "key", "button", "owner_id", "intent_token",
        "valid_until_ns", "release_call_started_ns", "release_call_returned_ns", "release_call_bracket_ns",
        "owner_transition_verified", "grants_input_authority", "lease_time_valid_at_request",
        "cancel_requested_at_request", "focus_invalid_at_request", "ordinary_release_candidate", "measurement_contract",
    ]
    release_required = ["event", "transition_schema", "operation", "<dynamic>", "owner_id", "intent_token", "valid_until_ns",
                        "release_call_started_ns", "release_call_returned_ns", "release_call_bracket_ns", "owner_transition_verified",
                        "grants_input_authority", "<dynamic>", "measurement_contract"]
    if v13_release != release_required:
        raise AssertionError(f"unexpected release schema: {v13_release}")
    if not {"schema", "event_sequence", "observed_ns", "kind", "polarity", "useful", "controller_visible", "before", "after"}.issubset(scorer):
        raise AssertionError(f"scorer schema missing required known fields: {scorer}")
    if "source_event_id" in scorer or "scorer_epoch_id" in scorer:
        raise AssertionError(f"scorer unexpectedly acquired an identity field: {scorer}")
    if "source_event_id" in v13_release or "scorer_epoch_id" in v13_release:
        raise AssertionError(f"release schema unexpectedly acquired cross-plane identity: {v13_release}")
    if "source_event_id" in v12_adapter:
        raise AssertionError(f"legacy adapter unexpectedly emits source_event_id: {v12_adapter}")
    if not all(checks.values()):
        raise AssertionError(f"source assertions failed: {[k for k, v in checks.items() if not v]}")

    return {
        "schema": "map01-task-effect-source-schema-result-v1",
        "allocation": "MAP01-TASK-EFFECT-SOURCE-SCHEMA-5126-20260928-01",
        "main_sha": FREEZE["main_sha"],
        "disposition": "HOLD_SOURCE_IDENTITY_INSUFFICIENT",
        "scope": "static source schema availability only; no runtime observation",
        "v13_release_receipt_keys": v13_release + ["key|button (operation-dependent)", "lease_state_at_request (expanded)"] ,
        "scorer_event_keys": scorer,
        "legacy_v12_adapter_edge_keys": v12_adapter,
        "legacy_internal_edge_ids_not_in_adapter": ["press_id", "release_id"],
        "checks": checks,
        "limitations": [
            "The v12 physical-edge owner is a retained historical dependency and is not asserted to be the active v13 input path.",
            "Static source inspection does not observe serialized live events or prove runtime collisions.",
            "The scorer event_sequence is local to one ProgressClock instance and restarts when a new instance is constructed.",
        ],
        "live_calls": 0,
        "gpu_calls": 0,
        "docker_calls": 0,
    }


def main() -> None:
    result = audit()
    (HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(HERE / "result.json"), "disposition": result["disposition"],
                      "checks_passed": sum(result["checks"].values()), "checks": len(result["checks"]),
                      "live_calls": 0, "gpu_calls": 0, "docker_calls": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
