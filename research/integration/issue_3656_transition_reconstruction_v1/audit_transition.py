"""Independent, read-only reconstruction of Issue #3652 formal-01 evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_KINDS = [
    "session_setup", "observe", "observe", "observe", "focus_drift",
    "stale_admission", "modal_transition", "modal_recovery",
    "geometry_transition", "stale_geometry_admission", "window_replacement",
    "stale_window_admission", "return_to_earlier_app", "stable_control",
    "process_cleanup",
]
ROLES = {"inkscape": "4194311", "calc": "8389413", "chromium": "6291459"}


def audit(raw: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    holds: list[str] = []
    events = raw.get("ledger")
    if not isinstance(events, list):
        events = []
        errors.append("ledger must be a list")

    kinds = [e.get("kind") if isinstance(e, dict) else None for e in events]
    if kinds != EXPECTED_KINDS:
        errors.append("ledger kinds/order do not match the exact 15-event protocol")
    if raw.get("event_count") != 15 or len(events) != 15:
        errors.append("event_count/ledger length must both equal 15")
    if [e.get("seq") for e in events if isinstance(e, dict)] != list(range(len(events))):
        errors.append("sequence numbers are not contiguous integers")

    for i, event in enumerate(events):
        if not isinstance(event, dict):
            errors.append(f"event {i} is not an object")
            continue
        payload = {k: v for k, v in event.items() if k != "hash"}
        expected = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        if event.get("hash") != expected:
            errors.append(f"event {i} hash mismatch")

    by_kind = {e.get("kind"): e for e in events if isinstance(e, dict)}
    initial: dict[str, str] = {}
    for role, expected_xid in ROLES.items():
        matches = [e for e in events if isinstance(e, dict) and e.get("kind") == "observe" and e.get("app") == role]
        if len(matches) != 1 or matches[0].get("window") != expected_xid:
            errors.append(f"initial {role} observation missing/ambiguous/mismatched")
        else:
            initial[role] = expected_xid
    apps = raw.get("apps", {})
    if set(apps) != set(ROLES):
        errors.append("application identity roles do not match the three preregistered roles")
    else:
        for role, xid in ROLES.items():
            info = apps[role]
            identity = info.get("identity", {})
            matches = identity.get("matches", [])
            if identity.get("status") != "READY" or len(matches) != 1 or str(matches[0].get("window")) != xid:
                errors.append(f"{role} identity receipt is not unique READY for its observed XID")
            if str(info.get("window")) != xid:
                errors.append(f"{role} app window does not match initial observation")

    def ev(kind: str) -> dict[str, Any]:
        value = by_kind.get(kind)
        return value if isinstance(value, dict) else {}

    drift, stale = ev("focus_drift"), ev("stale_admission")
    focus = (drift.get("from_app") == "calc" and drift.get("to_app") == "inkscape" and
             drift.get("active") == ROLES["inkscape"] and drift.get("input_emitted") is False and
             stale.get("app") == "calc" and stale.get("old_window") == ROLES["calc"] and
             stale.get("disposition") == "refused" and stale.get("input_emitted") is False)
    if not focus:
        holds.append("focus drift/stale refusal not fully supported by raw fields")

    modal, recovery = ev("modal_transition"), ev("modal_recovery")
    modal_ok = (modal.get("app") == "calc" and modal.get("parent") == ROLES["calc"] and
                modal.get("modal") is not None and modal.get("input_emitted") is True and
                recovery.get("app") == "calc" and recovery.get("modal") == modal.get("modal") and
                recovery.get("disposition") == "observe_only" and recovery.get("input_emitted") is True)
    if not modal_ok:
        holds.append("modal identity/recovery not fully supported by raw fields")

    geometry, stale_geom = ev("geometry_transition"), ev("stale_geometry_admission")
    geometry_ok = (geometry.get("app") == "calc" and geometry.get("old_geometry") != geometry.get("new_geometry") and
                   geometry.get("surface_generation") == 2 and stale_geom.get("app") == "calc" and
                   stale_geom.get("disposition") == "refused" and stale_geom.get("input_emitted") is False)
    if not geometry_ok:
        holds.append("geometry change/stale refusal not fully supported by raw fields")

    replacement, stale_window = ev("window_replacement"), ev("stale_window_admission")
    cleanup = replacement.get("old_process_cleanup", {})
    replacement_ok = (replacement.get("app") == "chromium" and
                      replacement.get("old_window") == replacement.get("new_window") == ROLES["chromium"] and
                      replacement.get("identity_reused") is True and
                      type(replacement.get("old_pid")) is int and type(replacement.get("new_pid")) is int and
                      replacement.get("old_pid") != replacement.get("new_pid") and
                      replacement.get("surface_generation") == 2 and
                      replacement.get("typed_identity") == {"pid": replacement.get("new_pid"),
                          "surface_generation": 2, "window": replacement.get("new_window")} and
                      cleanup.get("pid") == replacement.get("old_pid") and cleanup.get("remaining_pids") == [] and
                      stale_window.get("app") == "chromium" and stale_window.get("old_window") == ROLES["chromium"] and
                      stale_window.get("disposition") == "refused" and stale_window.get("input_emitted") is False)
    if not replacement_ok:
        holds.append("replacement typed identity/stale refusal not fully supported by raw fields")
    if "old_window_absent" not in replacement:
        holds.append("Chromium old-window-absence receipt is missing")

    returned, stable = ev("return_to_earlier_app"), ev("stable_control")
    return_ok = (returned.get("app") == "calc" and returned.get("window") == ROLES["calc"] and
                 returned.get("surface_generation") == 2 and returned.get("fresh_validation") is True and
                 stable.get("app") == "calc" and stable.get("action_dispatched") is False and
                 stable.get("independent_task_effect_scored") is False)
    if not return_ok:
        holds.append("Calc return/stable control not fully supported by raw fields")
    if "active_window" not in returned:
        holds.append("active-window observation at Calc return is missing")

    input_events = [e for e in events if isinstance(e, dict) and e.get("input_emitted") is True]
    input_kinds = ["modal_transition", "modal_recovery"]
    # The formal report says three operations, but the raw ledger only records
    # two event-level true booleans and does not enumerate/count operations.
    # Preserve the claimed count while marking this binding gap as HOLD.
    if type(raw.get("input_operations")) is not int or raw.get("input_operations") != 3:
        errors.append("input_operations must be the integer 3 (bool is not accepted)")
    if len(input_events) != 3:
        holds.append("raw does not provide three independently countable input-operation receipts")
    if [e.get("kind") for e in input_events] != input_kinds:
        holds.append("input-emitting event kinds do not map one-to-one to the three reported operations")
    if type(raw.get("model_calls")) is not int or raw.get("model_calls") != 0:
        errors.append("model_calls must be integer zero")
    if type(raw.get("network_calls")) is not int or raw.get("network_calls") != 0:
        errors.append("network_calls must be integer zero")
    process = ev("process_cleanup")
    if (process.get("complete") is not True or raw.get("cleanup_complete") is not True or
            raw.get("xvfb_socket_disappeared") is not True or
            not isinstance(process.get("processes"), list) or
            any(p.get("remaining_pids") != [] for p in process.get("processes", []) if isinstance(p, dict))):
        errors.append("process/Xvfb cleanup receipt is incomplete or has survivors")
    if not any(p.get("returncode") == 255 for p in process.get("processes", []) if isinstance(p, dict)):
        errors.append("disclosed LibreOffice return code 255 missing")

    # Runner checks are reported for comparison only; never used as evidence.
    if raw.get("checks") != [focus, modal_ok, geometry_ok, replacement_ok, return_ok]:
        errors.append("runner check vector differs from independently derived outcomes")
    outcome = "FAIL_AUDIT_MUTATION_ACCEPTED" if errors else (
        "HOLD_AUDIT_EVIDENCE_INCOMPLETE" if holds else "PASS_AUDIT_RECONSTRUCTION_SCOPED")
    return {"decision": outcome, "error_count": len(errors), "errors": errors,
            "hold_count": len(holds), "holds": holds,
            "derived_transitions": {"focus_drift": focus, "modal": modal_ok, "geometry": geometry_ok,
                                    "chromium_replacement": replacement_ok, "calc_return": return_ok},
            "runner_checks_used_as_evidence": False}


def main(path: str) -> int:
    raw_bytes = Path(path).read_bytes()
    raw = json.loads(raw_bytes)
    result = audit(raw)
    result["raw_sha256"] = hashlib.sha256(raw_bytes).hexdigest()
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["decision"] == "PASS_AUDIT_RECONSTRUCTION_SCOPED" else 1


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv[1]))
