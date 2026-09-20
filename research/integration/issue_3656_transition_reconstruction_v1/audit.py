"""Independent, read-only reconstruction of the Issue #3652 raw ledger."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ALLOCATION_ID = "issue2499-readiness-successor-3652-formal-01"
ISSUE_NUMBER = 3652
RAW_SHA256 = "f0df0248ff5e754a91e93271d9784f08d06ae1e8ff349b5f82f0fd015eb42883"
EXPECTED_KINDS = [
    "session_setup",
    "observe", "observe", "observe",
    "focus_drift", "stale_admission",
    "modal_transition", "modal_recovery",
    "geometry_transition", "stale_geometry_admission",
    "window_replacement", "stale_window_admission",
    "return_to_earlier_app", "stable_control",
    "process_cleanup",
]
ROLE_ORDER = ("inkscape", "calc", "chromium")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _event_hash(row: dict[str, Any]) -> str:
    payload = {key: value for key, value in row.items() if key != "hash"}
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return _sha(encoded)


def _strict_int(value: Any) -> bool:
    return type(value) is int


def _canonical_raw_digest(raw_bytes: bytes) -> tuple[str, str, bool]:
    """Return exact and LF-canonical digests, recognizing Git checkout CRLF."""
    exact = _sha(raw_bytes)
    if raw_bytes.count(b"\r") != raw_bytes.count(b"\r\n"):
        return exact, exact, False
    normalized_bytes = raw_bytes.replace(b"\r\n", b"\n")
    normalized = _sha(normalized_bytes)
    return exact, normalized, exact != normalized


def _has_exact_role(app: str, identity: Any) -> bool:
    if not isinstance(identity, dict) or identity.get("status") != "READY":
        return False
    matches = identity.get("matches")
    if not isinstance(matches, list) or len(matches) != 1:
        return False
    match = matches[0]
    if not isinstance(match, dict) or not isinstance(match.get("raw"), str):
        return False
    text = match["raw"].casefold()
    markers = {
        "inkscape": ("inkscape",),
        "calc": ("libreoffice-calc", "libreoffice calc"),
        "chromium": ("chromium",),
    }
    return any(marker in text for marker in markers[app])


def audit(raw: dict[str, Any], raw_bytes: bytes | None = None) -> dict[str, Any]:
    """Recompute what the raw supports; never use raw['checks'] as authority."""
    errors: list[str] = []
    evidence_gaps: list[str] = []
    derived: dict[str, str] = {}

    exact_raw_digest = None
    canonical_raw_digest = None
    checkout_line_endings_normalized = False
    if raw_bytes is not None:
        exact_raw_digest, canonical_raw_digest, checkout_line_endings_normalized = _canonical_raw_digest(raw_bytes)
        if canonical_raw_digest != RAW_SHA256:
            errors.append("frozen_raw_sha256_mismatch")
    if raw.get("allocation_id") != ALLOCATION_ID or raw.get("issue") != ISSUE_NUMBER:
        errors.append("allocation_identity_mismatch")
    if raw.get("formal_invocations") != 1 or raw.get("retries") != 0:
        errors.append("allocation_count_mismatch")
    if raw.get("decision") != "HOLD_TASK_EFFECT_UNTESTED":
        errors.append("predecessor_decision_mismatch")
    if raw.get("transition_gate") != "PASS_MIXED_APP_READINESS_TRANSITIONS_SCOPED":
        errors.append("predecessor_transition_gate_mismatch")
    if raw.get("session_complete") is not True:
        errors.append("session_not_complete")
    if raw.get("independent_task_effect_scored") is not False:
        errors.append("task_effect_scope_mismatch")
    if raw.get("model_calls") != 0 or raw.get("network_calls") != 0:
        errors.append("unexpected_model_or_network_activity")

    ledger = raw.get("ledger")
    if not isinstance(ledger, list):
        errors.append("ledger_missing_or_malformed")
        ledger = []
    kinds = [row.get("kind") if isinstance(row, dict) else None for row in ledger]
    if kinds != EXPECTED_KINDS:
        errors.append("ledger_event_order_or_cardinality_mismatch")
    if raw.get("event_count") != len(ledger) or len(ledger) != len(EXPECTED_KINDS):
        errors.append("event_count_mismatch")
    for index, row in enumerate(ledger):
        if not isinstance(row, dict) or not _strict_int(row.get("seq")) or row.get("seq") != index:
            errors.append(f"event_sequence_mismatch:{index}")
            continue
        if row.get("hash") != _event_hash(row):
            errors.append(f"event_hash_mismatch:{index}")

    if len(ledger) == len(EXPECTED_KINDS) and kinds == EXPECTED_KINDS:
        setup = ledger[0]
        observations = ledger[1:4]
        focus, stale_focus = ledger[4:6]
        modal, recovery = ledger[6:8]
        geometry, stale_geometry = ledger[8:10]
        replacement, stale_window = ledger[10:12]
        returned, stable, cleanup_event = ledger[12:15]

        if setup.get("xauthority_cookie_added") is not True or setup.get("xauthority_mode") != "cookie_auth_file":
            errors.append("xauthority_setup_not_verified")

        apps = raw.get("apps")
        if not isinstance(apps, dict) or set(apps) != set(ROLE_ORDER):
            errors.append("final_role_set_mismatch")
            apps = apps if isinstance(apps, dict) else {}
        for app in ROLE_ORDER:
            entry = apps.get(app)
            if not isinstance(entry, dict) or not _has_exact_role(app, entry.get("identity")):
                errors.append(f"final_identity_not_exactly_one:{app}")
                continue
            match = entry["identity"]["matches"][0]
            if str(match.get("window")) != str(entry.get("window")):
                errors.append(f"final_window_identity_mismatch:{app}")
            if not _strict_int(entry.get("pid")) or entry["pid"] <= 0:
                errors.append(f"launcher_pid_invalid:{app}")

        observed_apps = [row.get("app") for row in observations]
        if observed_apps != list(ROLE_ORDER):
            errors.append("initial_observation_role_order_mismatch")
        initial_windows = {row.get("app"): str(row.get("window")) for row in observations}
        if any(not _strict_int(row.get("surface_generation")) or row.get("surface_generation") != 1 for row in observations):
            errors.append("initial_surface_generation_mismatch")
        for app in ROLE_ORDER:
            if app in apps and str(apps[app].get("window")) != initial_windows.get(app):
                errors.append(f"window_changed_without_transition:{app}")

        # Transition 1: observed focus drift makes the old Calc capability stale.
        derived["focus_drift_and_refusal"] = (
            "PASS" if focus.get("from_app") == "calc"
            and focus.get("to_app") == "inkscape"
            and focus.get("active") == initial_windows.get("inkscape")
            and focus.get("input_emitted") is False
            and stale_focus.get("app") == "calc"
            and str(stale_focus.get("old_window")) == initial_windows.get("calc")
            and stale_focus.get("disposition") == "refused"
            and stale_focus.get("input_emitted") is False else "FAIL"
        )

        # Transition 2: one modal open and one observe-only dismissal.
        derived["modal_transition_and_recovery"] = (
            "PASS" if modal.get("app") == "calc"
            and str(modal.get("parent")) == initial_windows.get("calc")
            and modal.get("modal") is not None
            and modal.get("input_emitted") is True
            and recovery.get("app") == "calc"
            and recovery.get("modal") == modal.get("modal")
            and recovery.get("disposition") == "observe_only"
            and recovery.get("input_emitted") is True else "FAIL"
        )

        # Transition 3: changed geometry and refusal of the stale capability.
        derived["geometry_transition_and_refusal"] = (
            "PASS" if geometry.get("app") == "calc"
            and geometry.get("old_geometry")
            and geometry.get("new_geometry")
            and geometry.get("old_geometry") != geometry.get("new_geometry")
            and geometry.get("surface_generation") == 2
            and stale_geometry.get("app") == "calc"
            and stale_geometry.get("disposition") == "refused"
            and stale_geometry.get("input_emitted") is False else "FAIL"
        )
        if geometry.get("input_emitted") is not True:
            evidence_gaps.append("geometry_input_emission_receipt_missing")

        # Transition 4: replacement lineage is mostly present, but the raw lacks
        # the observed old-window-absent receipt required to establish ordering.
        old_pid = replacement.get("old_pid")
        new_pid = replacement.get("new_pid")
        old_window = str(replacement.get("old_window"))
        new_window = str(replacement.get("new_window"))
        chrome_final = apps.get("chromium", {})
        replacement_shape_ok = (
            replacement.get("app") == "chromium"
            and _strict_int(old_pid) and _strict_int(new_pid)
            and old_pid != new_pid
            and replacement.get("surface_generation") == 2
            and chrome_final.get("pid") == new_pid
            and str(chrome_final.get("window")) == new_window
            and replacement.get("identity_reused") is (old_window == new_window)
            and replacement.get("old_process_cleanup", {}).get("returncode") is not None
            and replacement.get("old_process_cleanup", {}).get("remaining_pids") == []
            and stale_window.get("app") == "chromium"
            and str(stale_window.get("old_window")) == old_window
            and stale_window.get("disposition") == "refused"
            and stale_window.get("input_emitted") is False
        )
        if replacement_shape_ok:
            if replacement.get("old_window_absent") is True:
                derived["window_replacement_and_refusal"] = "PASS"
            else:
                derived["window_replacement_and_refusal"] = "HOLD"
                evidence_gaps.append("old_window_absence_receipt_missing")
        else:
            derived["window_replacement_and_refusal"] = "FAIL"

        # Transition 5: a fresh Calc capability is recorded, but no active-window
        # observation is retained, so the runner's final boolean is insufficient.
        return_shape_ok = (
            returned.get("app") == "calc"
            and str(returned.get("window")) == str(apps.get("calc", {}).get("window"))
            and returned.get("surface_generation") == apps.get("calc", {}).get("surface_generation") == 2
            and returned.get("fresh_validation") is True
            and stable.get("app") == "calc"
            and stable.get("action_dispatched") is False
            and stable.get("independent_task_effect_scored") is False
        )
        if return_shape_ok:
            if str(returned.get("active_window")) == str(apps.get("calc", {}).get("window")):
                derived["return_to_earlier_app"] = "PASS"
            else:
                derived["return_to_earlier_app"] = "HOLD"
                evidence_gaps.append("return_active_window_receipt_missing_or_mismatch")
        else:
            derived["return_to_earlier_app"] = "FAIL"

        # Inputs should be independently represented at the operation boundary:
        # modal open, modal close, and geometry resize, with no stable task action.
        emitted = sum(
            row.get("input_emitted") is True
            for row in (focus, stale_focus, modal, recovery, geometry, stale_geometry, replacement, stale_window)
        )
        if not _strict_int(raw.get("input_operations")) or raw.get("input_operations") != 3:
            errors.append("input_operation_count_mismatch")
        if emitted > 3:
            errors.append("input_event_receipt_count_exceeds_preregistered_operations")
        elif emitted < 3:
            evidence_gaps.append("input_emission_receipt_count_incomplete")
        if stable.get("action_dispatched") is not False:
            errors.append("unexpected_stable_task_action")

        cleanup_processes = raw.get("cleanup_processes")
        if raw.get("cleanup_complete") is not True or raw.get("xvfb_socket_disappeared") is not True:
            errors.append("cleanup_or_socket_not_verified")
        if cleanup_event.get("complete") is not True or cleanup_event.get("processes") != cleanup_processes:
            errors.append("cleanup_event_mismatch")
        if not isinstance(cleanup_processes, list) or len(cleanup_processes) != 5:
            errors.append("cleanup_process_group_count_mismatch")
        else:
            for process in cleanup_processes:
                if (not isinstance(process, dict)
                        or not _strict_int(process.get("pid"))
                        or type(process.get("returncode")) is not int
                        or process.get("remaining_pids") != []):
                    errors.append("cleanup_process_group_unreconciled")
                    break
            cleaned_pids = {process.get("pid") for process in cleanup_processes if isinstance(process, dict)}
            for app in ROLE_ORDER:
                pid = apps.get(app, {}).get("pid")
                if pid not in cleaned_pids:
                    errors.append(f"application_launcher_not_in_cleanup:{app}")

        if raw.get("event_count") != 15:
            errors.append("expected_15_ledger_events")

    complete_derived_pass = set(derived) == {
        "focus_drift_and_refusal", "modal_transition_and_recovery",
        "geometry_transition_and_refusal", "window_replacement_and_refusal",
        "return_to_earlier_app",
    } and all(value == "PASS" for value in derived.values())
    if any(value == "FAIL" for value in derived.values()):
        errors.append("transition_receipt_contradicts_preregistered_outcome")

    if errors:
        decision = "FAIL_AUDIT_RAW_INTEGRITY"
    elif evidence_gaps or not complete_derived_pass:
        decision = "HOLD_AUDIT_EVIDENCE_INCOMPLETE"
    else:
        decision = "PASS_AUDIT_RECONSTRUCTION_SCOPED"

    return {
        "schema": "issue-3660/independent-transition-audit-v1",
        "decision": decision,
        "errors": errors,
        "evidence_gaps": sorted(set(evidence_gaps)),
        "derived_transitions": derived,
        "runner_checks_observed_but_not_used": raw.get("checks"),
        "raw_sha256": exact_raw_digest,
        "canonical_lf_raw_sha256": canonical_raw_digest,
        "checkout_line_endings_normalized": checkout_line_endings_normalized,
    }


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m ...audit RAW_RESULT.json")
    path = Path(sys.argv[1])
    raw_bytes = path.read_bytes()
    raw = json.loads(raw_bytes)
    result = audit(raw, raw_bytes)
    print(json.dumps(result, sort_keys=True, indent=2))
    if result["decision"] == "FAIL_AUDIT_RAW_INTEGRITY":
        return 2
    if result["decision"] == "HOLD_AUDIT_EVIDENCE_INCOMPLETE":
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
