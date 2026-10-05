"""Run source-pinned positive and negative test-double cases for adapter v2."""

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from research.live_control.integrated_efficiency_compiled_adapter_v2 import (
    EXPECTED_METHOD_CONTRACT, compile_form_method,
)
from runtime.core_v1.compiled_gui import run as run_compiled

SOURCES = {
    "adapter_v2": ("research/live_control/integrated_efficiency_compiled_adapter_v2.py",
                   "f1f3f6b2a1f0487a9c6f65b51936fafc8b6101390b1e4070f8e31f741a28b6ef"),
    "compiled_core": ("runtime/core_v1/compiled_gui.py",
                      "d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014"),
}


def run_case(exact_value_after_entry):
    predicates = [
        {"field_pixels_changed": False, "field_value_matches_task": False,
         "field_target_present": True, "submit_target_present": True,
         "submission_pixels_changed": False},
        {"field_pixels_changed": True, "field_value_matches_task": exact_value_after_entry,
         "field_target_present": True, "submit_target_present": True,
         "submission_pixels_changed": False},
    ]
    if exact_value_after_entry:
        predicates.append({
            "field_pixels_changed": True, "field_value_matches_task": True,
            "field_target_present": True, "submit_target_present": True,
            "submission_pixels_changed": True,
        })
    sequence = 0
    actions, effect_calls = [], []
    interface = compile_form_method(
        interface_id="a07-exact-value-v2", session_scope="private-test-double-v1",
        surface="form", field_handle="field-ref", submit_handle="submit-ref",
        method_contract=EXPECTED_METHOD_CONTRACT)

    def observe(_payload):
        nonlocal sequence
        sequence += 1
        row = predicates[sequence - 1]
        return {"sequence": sequence, "captured_ns": time.perf_counter_ns(),
                "surface": "form", "predicates": row,
                "evidence_ref": f"frame-{sequence}",
                "evidence_digest": f"digest-{sequence}"}

    def execute(payload):
        actions.append(payload["operation"])
        return {"status": "completed", "action_id": f"action-{len(actions)}",
                "effect_ref": f"effect-{len(actions)}",
                "release": {"verified": True, "keys_down": [], "buttons_down": []}}

    def verify_effect(payload):
        effect_calls.append(payload["action"])
        return {"status": "succeeded", "evidence_ref": payload["observation"]["evidence_ref"]}

    receipt = run_compiled(interface, {
        "observe": observe,
        "admit": lambda payload: {
            "eligible": True, "status": "revalidated", "authorization": "one-use",
            "expected_sequence": payload["observation"]["sequence"],
            "valid_until_ns": time.perf_counter_ns() + 1_000_000_000,
        },
        "execute": execute, "verify_effect": verify_effect,
        "cancelled": lambda: False,
    })
    return {"exact_value_after_entry": exact_value_after_entry,
            "actions": actions, "effect_verifier_calls": effect_calls,
            "receipt": receipt}


def main():
    source_hashes = {name: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
                     for name, (path, _expected) in SOURCES.items()}
    source_hashes["runner"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    expected = {name: digest for name, (_path, digest) in SOURCES.items()}
    if {name: source_hashes[name] for name in SOURCES} != expected:
        raise SystemExit(f"source freeze mismatch: {source_hashes}")
    raw = {
        "schema": "compiled-form-exact-value-gate-a07-v1",
        "source_sha256": source_hashes,
        "scope": "test-double construction only; no observer/image/GUI/model/input/network calls",
        "cases": {"mismatch": run_case(False), "exact_match": run_case(True)},
    }
    Path(sys.argv[1]).write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n",
                                 encoding="utf-8")


if __name__ == "__main__":
    main()
