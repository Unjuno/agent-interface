#!/usr/bin/env python3
"""Strict, read-only reconstruction of the frozen #3652 transition ledger.

This auditor deliberately returns HOLD for transitions whose necessary receipt
was never retained. Runner booleans are never used as proof.
"""
import hashlib
import json
import sys
from pathlib import Path

EXPECTED_KINDS = [
    "session_setup", "observe", "observe", "observe", "focus_drift",
    "stale_admission", "modal_transition", "modal_recovery",
    "geometry_transition", "stale_geometry_admission", "window_replacement",
    "stale_window_admission", "return_to_earlier_app", "stable_control",
    "process_cleanup",
]


def audit(raw):
    errors, gaps = [], []
    events = raw.get("ledger")
    if not isinstance(events, list):
        return {"decision": "FAIL_AUDIT_INTEGRITY", "errors": ["ledger_not_list"], "gaps": []}
    kinds = [e.get("kind") if isinstance(e, dict) else None for e in events]
    if kinds != EXPECTED_KINDS:
        errors.append("event_protocol_order_or_cardinality_mismatch")
    if [e.get("seq") for e in events if isinstance(e, dict)] != list(range(len(events))):
        errors.append("sequence_discontinuity")
    for i, event in enumerate(events):
        if not isinstance(event, dict):
            errors.append(f"event_not_object:{i}")
            continue
        body = dict(event)
        claimed = body.pop("hash", None)
        actual = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        if claimed != actual:
            errors.append(f"event_hash_mismatch:{i}")
    if raw.get("event_count") != len(events):
        errors.append("event_count_mismatch")
    if raw.get("input_operations") != 3 or type(raw.get("input_operations")) is not int:
        errors.append("input_operation_count_mismatch")
    marked_input_events = sum(1 for e in events if isinstance(e, dict) and e.get("input_emitted") is True)
    if marked_input_events != raw.get("input_operations"):
        gaps.append("event_level_input_operation_receipt_count_mismatch")
    if raw.get("formal_invocations") != 1 or type(raw.get("formal_invocations")) is not int:
        errors.append("formal_invocation_count_mismatch")
    if raw.get("retries") != 0 or type(raw.get("retries")) is not int:
        errors.append("retry_count_mismatch")
    if raw.get("model_calls") != 0 or raw.get("network_calls") != 0:
        errors.append("unexpected_model_or_network_activity")

    by_kind = {k: [e for e in events if isinstance(e, dict) and e.get("kind") == k]
               for k in set(kinds)}
    def one(kind):
        found = by_kind.get(kind, [])
        return found[0] if len(found) == 1 else {}

    apps = raw.get("apps", {})
    roles = {"inkscape", "calc", "chromium"}
    if set(apps) != roles:
        errors.append("role_set_mismatch")
    initial = {}
    for role in sorted(roles & set(apps)):
        info = apps[role]
        ident = info.get("identity", {})
        matches = ident.get("matches", [])
        if ident.get("status") != "READY" or len(matches) != 1:
            errors.append(f"role_identity_not_unique:{role}")
            continue
        win = str(info.get("window"))
        if win != str(matches[0].get("window")):
            errors.append(f"role_window_identity_mismatch:{role}")
        initial[role] = win
    if len(initial) == 3 and len(set(initial.values())) != 3:
        errors.append("initial_role_windows_not_distinct")
    observations = [e for e in events if isinstance(e, dict) and e.get("kind") == "observe"]
    if [(e.get("app"), str(e.get("window")), e.get("surface_generation")) for e in observations] != [
        ("inkscape", initial.get("inkscape"), 1),
        ("calc", initial.get("calc"), 1),
        ("chromium", initial.get("chromium"), 1),
    ]:
        errors.append("initial_observation_role_binding_mismatch")

    focus, stale = one("focus_drift"), one("stale_admission")
    if not (focus.get("from_app") == "calc" and focus.get("to_app") == "inkscape"
            and focus.get("active") == initial.get("inkscape")
            and focus.get("active") != initial.get("calc")
            and focus.get("input_emitted") is False
            and stale.get("app") == "calc" and stale.get("old_window") == initial.get("calc")
            and stale.get("disposition") == "refused" and stale.get("input_emitted") is False):
        errors.append("focus_transition_raw_receipts_invalid")

    modal, recovery = one("modal_transition"), one("modal_recovery")
    if not (modal.get("app") == "calc" and modal.get("parent") == initial.get("calc")
            and modal.get("modal") and modal.get("input_emitted") is True
            and recovery.get("app") == "calc" and recovery.get("modal") == modal.get("modal")
            and recovery.get("disposition") == "observe_only"
            and recovery.get("input_emitted") is True):
        errors.append("modal_transition_raw_receipts_invalid")
    # No owner/parent relation or post-Escape disappearance receipt was retained.
    gaps.append("modal_owner_and_disappearance_not_independently_recorded")

    geometry, stale_geom = one("geometry_transition"), one("stale_geometry_admission")
    if not (geometry.get("app") == "calc" and geometry.get("old_geometry") != geometry.get("new_geometry")
            and geometry.get("surface_generation") == 2
            and stale_geom.get("app") == "calc" and stale_geom.get("disposition") == "refused"
            and stale_geom.get("input_emitted") is False):
        errors.append("geometry_transition_raw_receipts_invalid")

    replace, stale_window = one("window_replacement"), one("stale_window_admission")
    if not (replace.get("app") == "chromium" and replace.get("old_window") == replace.get("new_window")
            and replace.get("identity_reused") is True and replace.get("old_pid") != replace.get("new_pid")
            and replace.get("surface_generation") == 2):
        errors.append("replacement_identity_receipts_invalid")
    if not (stale_window.get("app") == "chromium" and stale_window.get("old_window") == replace.get("old_window")
            and stale_window.get("disposition") == "refused" and stale_window.get("input_emitted") is False):
        errors.append("stale_window_receipt_invalid")
    # The raw has no old-window absence receipt and no invoked generation-aware
    # admission request; a recorded disposition alone is not an experiment.
    gaps.append("chromium_stale_generation_admission_not_exercised_or_receipted")

    returned, stable = one("return_to_earlier_app"), one("stable_control")
    if not (returned.get("app") == "calc" and returned.get("window") == initial.get("calc")
            and returned.get("surface_generation") == 2):
        errors.append("calc_return_raw_receipts_invalid")
    if not (stable.get("app") == "calc" and stable.get("action_dispatched") is False
            and stable.get("independent_task_effect_scored") is False):
        errors.append("stable_control_raw_receipts_invalid")
    gaps.append("calc_return_active_window_and_fresh_role_resolution_not_recorded")

    cleanup = one("process_cleanup")
    processes = cleanup.get("processes", [])
    if not (cleanup.get("complete") is True and raw.get("cleanup_complete") is True
            and raw.get("xvfb_socket_disappeared") is True
            and all(p.get("returncode") is not None and not p.get("remaining_pids") for p in processes)):
        errors.append("cleanup_receipts_invalid")
    if raw.get("decision") != "HOLD_TASK_EFFECT_UNTESTED" or raw.get("independent_task_effect_scored") is not False:
        errors.append("scope_disposition_invalid")
    return {"decision": "FAIL_AUDIT_INTEGRITY" if errors else
            ("HOLD_AUDIT_EVIDENCE_INCOMPLETE" if gaps else "PASS_AUDIT_RECONSTRUCTION_SCOPED"),
            "errors": errors, "gaps": gaps, "event_count": len(events)}


def main():
    raw_path = Path(sys.argv[1])
    raw = json.loads(raw_path.read_text())
    result = audit(raw)
    result["raw_sha256"] = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
