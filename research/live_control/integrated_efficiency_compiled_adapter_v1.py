"""Compile validated six-task form grounding and handles into compiled GUI v1."""

from runtime.core_v1.compiled_gui import validate


EXPECTED_METHOD_CONTRACT = {
    "first_action": "enter_exact_token",
    "continue_when": "field_pixels_changed_and_submit_revalidated",
    "second_action": "activate_submit",
    "complete_when": "submission_pixels_changed_then_independent_score",
}


def compile_form_method(*, interface_id, session_scope, surface,
                        field_handle, submit_handle, method_contract):
    """Build the bounded form graph only for the frozen two-step method."""
    for value, label in (
            (interface_id, "interface_id"), (session_scope, "session_scope"),
            (surface, "surface"), (field_handle, "field_handle"),
            (submit_handle, "submit_handle")):
        if type(value) is not str or not value:
            raise ValueError(f"nonempty {label} required")
    if field_handle == submit_handle:
        raise ValueError("field and submit handles must be distinct")
    if type(method_contract) is not dict or method_contract != EXPECTED_METHOD_CONTRACT:
        raise ValueError("validated effect-gated form method required")

    interface = {
        "format": "compiled-gui-interface-v1",
        "interface_id": interface_id,
        "session_scope": session_scope,
        "surface": surface,
        "predicates": ["field_pixels_changed", "field_target_present",
                       "submit_target_present", "submission_pixels_changed"],
        "symbols": {
            "value_field": {
                "kind": "target_reference", "target_reference": field_handle,
                "identity_predicate": "field_target_present",
                "dependencies": ["field_target_present", "field_pixels_changed"],
            },
            "submit_control": {
                "kind": "target_reference", "target_reference": submit_handle,
                "identity_predicate": "submit_target_present",
                "dependencies": ["submit_target_present", "field_pixels_changed"],
            },
        },
        "actions": {
            "enter_token": {
                "target_symbol": "value_field", "operation": "enter_exact_token",
                "expected_effect": {"field_pixels_changed": True},
            },
            "submit_form": {
                "target_symbol": "submit_control", "operation": "activate_submit",
                "expected_effect": {"submission_pixels_changed": True},
            },
        },
        "method": {
            "name": "enter_then_submit", "version": "1",
            "initial_state": "empty", "max_transitions": 2,
            "max_runtime_ms": 10_000,
            "states": {
                "empty": {"branches": [{
                    "when": {"field_pixels_changed": False,
                             "field_target_present": True},
                    "outcome": "action", "action": "enter_token",
                    "next_state": "filled", "reason": None,
                }]},
                "filled": {"branches": [{
                    "when": {"field_pixels_changed": True,
                             "submit_target_present": True},
                    "outcome": "action", "action": "submit_form",
                    "next_state": "submitted", "reason": None,
                }]},
                "submitted": {"branches": [{
                    "when": {"submission_pixels_changed": True},
                    "outcome": "complete", "action": None,
                    "next_state": None, "reason": None,
                }]},
            },
        },
    }
    return validate(interface)
