"""Frozen test-double counterexample: pixel change does not prove field content."""

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from research.live_control.integrated_efficiency_compiled_adapter_v1 import compile_form_method
from runtime.core_v1.compiled_gui import run as run_compiled


SOURCES = {
    "caller": ("research/live_control/adaptive_acquisition_caller_v3.py",
               "8517d130d7336b27e6ddfc0ee06629d2b1183070cf845c3ef4ada8adc3cd79ca"),
    "compiled": ("runtime/core_v1/compiled_gui.py",
                 "d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014"),
    "adapter": ("research/live_control/integrated_efficiency_compiled_adapter_v1.py",
                 "0856ad8d7a522ee239040e0c878d43472e6211a7360e4dad3195032fac9d713e"),
}
CONTRACT = {
    "first_action": "enter_exact_token",
    "continue_when": "field_pixels_changed_and_submit_revalidated",
    "second_action": "activate_submit",
    "complete_when": "submission_pixels_changed_then_independent_score",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source_hashes = {name: sha(ROOT / path) for name, (path, _expected) in SOURCES.items()}
    expected_hashes = {name: expected for name, (_path, expected) in SOURCES.items()}
    if source_hashes != expected_hashes:
        raise SystemExit(f"source freeze mismatch: {source_hashes}")

    interface = compile_form_method(
        interface_id="a06-semantic-counterexample-v1",
        session_scope="private-test-double-v1", surface="form",
        field_handle="field-ref", submit_handle="submit-ref",
        method_contract=CONTRACT)
    actions = []
    sequence = 0

    def observe(payload):
        nonlocal sequence
        sequence += 1
        # The requested value remains absent, despite a change in field pixels.
        return {
            "sequence": sequence, "captured_ns": time.perf_counter_ns(),
            "surface": "form", "evidence_ref": f"frame-{sequence}",
            "evidence_digest": f"synthetic-frame-{sequence}",
            "predicates": {
                "field_pixels_changed": sequence > 1,
                "field_target_present": True,
                "submit_target_present": True,
                "submission_pixels_changed": sequence > 2,
            },
        }

    receipt = run_compiled(interface, {
        "observe": observe,
        "admit": lambda payload: {
            "eligible": True, "status": "revalidated", "authorization": "one-use",
            "expected_sequence": payload["observation"]["sequence"],
            "valid_until_ns": time.perf_counter_ns() + 1_000_000_000,
        },
        "execute": lambda action: actions.append(action["operation"]) or {
            "status": "completed", "action_id": f"action-{len(actions)}",
            "effect_ref": f"effect-{len(actions)}",
            "release": {"verified": True, "keys_down": [], "buttons_down": []},
        },
        "verify_effect": lambda payload: {
            "status": "succeeded", "evidence_ref": payload["observation"]["evidence_ref"],
        },
        "cancelled": lambda: False,
        "journal": lambda _event: None,
    })
    result = {
        "schema": "compiled-form-field-semantic-counterexample-a06-v1",
        "source_sha256": source_hashes,
        "scenario": {
            "expected_field_value": "task-token-991081-1",
            "observed_field_value": "",
            "field_pixels_changed_after_entry": True,
            "submit_target_present": True,
        },
        "actions": actions,
        "compiled_receipt": receipt,
        "disposition": "FAIL_FIELD_SEMANTIC_PREDICATE" if "activate_submit" in actions else "NO_COUNTEREXAMPLE",
    }
    Path(sys.argv[1]).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
