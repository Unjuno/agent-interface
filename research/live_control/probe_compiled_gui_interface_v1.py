"""Deterministic mechanics probe for compiled GUI local continuation v1."""
import copy
import hashlib
import json
from pathlib import Path

from adaptive_acquisition_caller_v1 import run as run_adaptive
from compiled_gui_interface_v1 import run, validate


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/compiled-gui-interface-01"


class Clock:
    def __init__(self):
        self.value = 1_000_000

    def __call__(self):
        self.value += 100
        return self.value


def interface():
    return {
        "format": "compiled-gui-interface-v1",
        "interface_id": "calc-confirm-save-v1",
        "session_scope": "offline-calc-fixture",
        "surface": "calc-window",
        "predicates": ["document_dirty", "confirm_dialog",
                       "save_target_present", "confirm_target_present"],
        "symbols": {
            "save_control": {
                "kind": "target_reference", "target_reference": "handle:save",
                "identity_predicate": "save_target_present",
                "dependencies": ["save_target_present", "confirm_dialog"],
            },
            "confirm_control": {
                "kind": "target_reference", "target_reference": "handle:confirm",
                "identity_predicate": "confirm_target_present",
                "dependencies": ["confirm_target_present", "confirm_dialog"],
            },
        },
        "actions": {
            "request_save": {"target_symbol": "save_control",
                             "operation": "activate_save",
                             "expected_effect": {"confirm_dialog": "present"}},
            "confirm_save": {"target_symbol": "confirm_control",
                             "operation": "activate_confirm",
                             "expected_effect": {"document_dirty": False,
                                                 "confirm_dialog": "absent"}},
        },
        "method": {
            "name": "save_with_confirmation", "version": "1",
            "initial_state": "editing", "max_transitions": 2,
            "max_runtime_ms": 1000,
            "states": {
                "editing": {"branches": [{
                    "when": {"document_dirty": True, "confirm_dialog": "absent",
                             "save_target_present": True},
                    "outcome": "action", "action": "request_save",
                    "next_state": "confirming", "reason": None}]},
                "confirming": {"branches": [{
                    "when": {"document_dirty": True, "confirm_dialog": "present",
                             "confirm_target_present": True},
                    "outcome": "action", "action": "confirm_save",
                    "next_state": "done", "reason": None}]},
                "done": {"branches": [{
                    "when": {"document_dirty": False, "confirm_dialog": "absent"},
                    "outcome": "complete", "action": None,
                    "next_state": None, "reason": None}]},
            },
        },
    }


def obs(sequence, dirty, dialog, *, digest=None, surface="calc-window"):
    return {
        "sequence": sequence, "captured_ns": 2_000_000 + sequence,
        "surface": surface,
        "predicates": {
            "document_dirty": dirty,
            "confirm_dialog": dialog,
            "save_target_present": True,
            "confirm_target_present": dialog == "present",
        },
        "evidence_ref": f"frame:{sequence}",
        "evidence_digest": digest or f"digest:{sequence}:{dirty}:{dialog}",
    }


POSITIVE = [obs(1, True, "absent"), obs(2, True, "present"),
            obs(3, False, "absent")]


def execute_case(observations, *, admissions=None, effects=None, terminals=None,
                 cancel_at=None, spec=None):
    observations = copy.deepcopy(observations)
    admissions = list(admissions or ["revalidated"] * 8)
    effects = list(effects or ["succeeded"] * 8)
    terminals = list(terminals or ["completed"] * 8)
    calls = {"observe": [], "admit": [], "execute": [], "verify_effect": [],
             "cancelled": 0, "journal": []}

    def observe(payload):
        calls["observe"].append(copy.deepcopy(payload))
        return observations.pop(0)

    def admit(payload):
        calls["admit"].append(copy.deepcopy(payload))
        status = admissions.pop(0)
        eligible = status == "revalidated"
        return {"eligible": eligible, "status": status,
                "authorization": f"private:{len(calls['admit'])}" if eligible else None,
                "expected_sequence": payload["observation"]["sequence"],
                "valid_until_ns": 10_000_000_000}

    def execute(payload):
        calls["execute"].append(copy.deepcopy(payload))
        status = terminals.pop(0)
        release = {"verified": status != "release_failed",
                   "keys_down": [], "buttons_down": []}
        return {"status": "completed" if status == "release_failed" else status,
                "action_id": f"action:{len(calls['execute'])}",
                "effect_ref": f"effect:{len(calls['execute'])}",
                "release": release}

    def verify_effect(payload):
        calls["verify_effect"].append(copy.deepcopy(payload))
        return {"status": effects.pop(0),
                "evidence_ref": payload["observation"]["evidence_ref"]}

    def cancelled():
        calls["cancelled"] += 1
        return cancel_at is not None and calls["cancelled"] == cancel_at

    adapters = {"observe": observe, "admit": admit, "execute": execute,
                "verify_effect": verify_effect, "cancelled": cancelled,
                "journal": calls["journal"].append}
    result = run(spec or interface(), adapters, clock=Clock())
    return result, calls


def refused(mutator):
    candidate = interface()
    mutator(candidate)
    try:
        validate(candidate)
    except (TypeError, ValueError):
        return True
    return False


def adaptive_case(route):
    compiled = interface()
    selected = {"interface": compiled, "authority": "reference_only"}
    runtime_receipts = []

    def local_execute(payload):
        receipt, _ = execute_case(POSITIVE, spec=payload["target"]["interface"])
        runtime_receipts.append(receipt)
        return {"status": "completed" if receipt["outcome"] == "TASK_SUCCEEDED"
                else "failed"}

    adapters = {
        "observe_source": lambda payload: {"frame": "synthetic-calc"},
        "coarse_model": lambda payload: {
            "call_id": "synthetic:coarse", "usage": None, "cost": None,
            "requested_model": "test-double", "requested_effort": "none",
            "output": {"status": "candidate", "point": [1, 1]}},
        "acquire_anchor": lambda payload: {"receipt": "synthetic-anchor"},
        "anchor_model": lambda payload: {
            "call_id": "synthetic:compile", "usage": None, "cost": None,
            "requested_model": "test-double", "requested_effort": "none",
            "output": {"status": "target_reference", "target": selected}},
        "reuse_revalidate": lambda payload: {"status": "revalidated"},
        "acquire_expansion": lambda payload: {"receipts": []},
        "expanded_model": lambda payload: (_ for _ in ()).throw(
            AssertionError("unexpected repair model call")),
        "final_revalidate": lambda payload: {"status": "revalidated"},
        "execute": local_execute,
        "verify_effect": lambda payload: {"status": "succeeded"},
    }
    if route == "cold":
        specification = {"target": "save Calc document", "route": "cold",
            "coarse_origin": "model_produced", "provided_coarse": None,
            "cached_target": None, "repair_on": [],
            "session_id": "compiled-interface-offline"}
        ids = iter(["attempt:coarse", "attempt:compile"]).__next__
    else:
        specification = {"target": "save Calc document", "route": "reuse",
            "coarse_origin": "caller_provided", "provided_coarse": None,
            "cached_target": selected, "repair_on": [],
            "session_id": "compiled-interface-offline"}
        ids = None
    result = run_adaptive(specification, adapters, clock=Clock(), id_factory=ids)
    return result, runtime_receipts[0]


def main():
    scenarios = {}
    calls = {}

    scenarios["positive-two-dependent-actions"], calls["positive"] = execute_case(POSITIVE)
    positive = scenarios["positive-two-dependent-actions"]
    assert positive["outcome"] == "TASK_SUCCEEDED"
    assert positive["completed_transitions"] == 2
    assert positive["frontier_model_resumptions"] == 0
    assert [row["action"] for row in positive["transitions"]] == [
        "request_save", "confirm_save"]
    assert positive["transitions"][1]["matched_conditions"]["confirm_dialog"] == "present"
    assert positive["transitions"][1]["observation_sequence"] == 2

    unknown_observation = obs(2, True, "present")
    unknown_observation["predicates"]["confirm_target_present"] = False
    scenarios["unknown-intermediate-state"], calls["unknown"] = execute_case(
        [POSITIVE[0], unknown_observation])
    assert scenarios["unknown-intermediate-state"]["reason"] == "unknown_state"
    assert len(calls["unknown"]["execute"]) == 1

    scenarios["stale-second-symbol"], calls["stale_symbol"] = execute_case(
        POSITIVE[:2], admissions=["revalidated", "stale"])
    assert scenarios["stale-second-symbol"]["reason"] == "stale_symbol"
    assert len(calls["stale_symbol"]["execute"]) == 1

    ambiguous_spec = interface()
    ambiguous_spec["method"]["states"]["editing"]["branches"].append(copy.deepcopy(
        ambiguous_spec["method"]["states"]["editing"]["branches"][0]))
    scenarios["ambiguous-branch"], calls["ambiguous"] = execute_case(
        [POSITIVE[0]], spec=ambiguous_spec)
    assert scenarios["ambiguous-branch"]["reason"] == "ambiguous_state"
    assert calls["ambiguous"]["execute"] == []

    unchanged = copy.deepcopy(POSITIVE[1])
    unchanged["evidence_digest"] = POSITIVE[0]["evidence_digest"]
    scenarios["no-progress"], calls["no_progress"] = execute_case(
        [POSITIVE[0], unchanged])
    assert scenarios["no-progress"]["reason"] == "no_progress"
    assert len(calls["no_progress"]["execute"]) == 1

    for status in ("failed", "unavailable"):
        name = "effect-" + status
        scenarios[name], calls[name] = execute_case(POSITIVE[:2], effects=[status])
        assert scenarios[name]["reason"] == "effect_" + status
        assert len(calls[name]["execute"]) == 1

    scenarios["cancel-before-second-admission"], calls["cancel"] = execute_case(
        POSITIVE[:2], cancel_at=5)
    assert scenarios["cancel-before-second-admission"]["reason"] == "cancelled"
    assert len(calls["cancel"]["execute"]) == 1

    budget_spec = interface()
    budget_spec["method"]["max_transitions"] = 1
    scenarios["transition-budget"], calls["budget"] = execute_case(
        POSITIVE[:2], spec=budget_spec)
    assert scenarios["transition-budget"]["reason"] == "budget_exhausted"
    assert len(calls["budget"]["execute"]) == 1

    scenarios["delivery-uncertain"], calls["delivery"] = execute_case(
        [POSITIVE[0]], terminals=["delivery_uncertain"])
    assert scenarios["delivery-uncertain"]["reason"] == "delivery_uncertain"

    scenarios["release-failure"], calls["release"] = execute_case(
        [POSITIVE[0]], terminals=["release_failed"])
    assert scenarios["release-failure"]["outcome"] == "RUNTIME_FAILED"

    scenarios["stale-observation"], calls["stale_observation"] = execute_case(
        [POSITIVE[0], {**POSITIVE[1], "sequence": 1}])
    assert scenarios["stale-observation"]["reason"] == "stale_observation"

    scenarios["surface-association-change"], calls["association"] = execute_case(
        [POSITIVE[0], obs(2, True, "present", surface="other-window")])
    assert scenarios["surface-association-change"]["reason"] == "association_changed"

    cold, cold_runtime = adaptive_case("cold")
    scenarios["adaptive-cold"] = {"adaptive": cold, "runtime": cold_runtime}
    assert cold["outcome"] == "TASK_SUCCEEDED"
    assert cold["accounting"]["attempted_calls"] == 2
    assert cold_runtime["completed_transitions"] == 2

    warm, warm_runtime = adaptive_case("reuse")
    scenarios["adaptive-warm"] = {"adaptive": warm, "runtime": warm_runtime}
    assert warm["outcome"] == "TASK_SUCCEEDED"
    assert warm["accounting"]["attempted_calls"] == 0
    assert warm_runtime["completed_transitions"] == 2

    controls = {
        "symbol_carries_authority": refused(lambda x: x["symbols"]["save_control"].update(
            authority="forbidden")),
        "duplicate_predicate": refused(lambda x: x["predicates"].append("document_dirty")),
        "unknown_action_symbol": refused(lambda x: x["actions"]["request_save"].update(
            target_symbol="missing")),
        "untyped_yield": refused(lambda x: x["method"]["states"]["editing"]["branches"][0].update(
            outcome="yield", action=None, next_state=None, reason="guess")),
    }
    assert all(controls.values())

    source_paths = [HERE / "compiled_gui_interface_v1.py", Path(__file__),
                    HERE / "adaptive_acquisition_caller_v1.py"]
    report = {
        "passed": True,
        "scenarios": scenarios,
        "adapter_call_counts": {name: {key: (value if key == "cancelled" else len(value))
                                        for key, value in row.items() if key != "journal"}
                                for name, row in calls.items()},
        "invalid_controls": controls,
        "sources": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in source_paths},
        "decision": "ADVANCE_TO_PREREGISTERED_LIVE_DESKTOP_BLOCK",
        "scope": ("deterministic local state-machine and shared-caller test doubles; "
                  "no GUI input, frontier model call, token/latency saving, live efficacy, "
                  "portability or break-even claim"),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    print("compiled_gui_interface_v1_probe_passed")


if __name__ == "__main__":
    main()
