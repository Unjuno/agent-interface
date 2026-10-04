"""Corrective identity-bound audit; the retained audit-v1 result stays unchanged."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def audit(raw_bytes, raw, freeze, probe_bytes, expectations):
    errors = []
    probe_sha = hashlib.sha256(probe_bytes).hexdigest()
    if probe_sha != freeze.get("probe_sha256"):
        errors.append("probe SHA mismatch")
    if raw.get("source_sha256") != probe_sha:
        errors.append("raw source SHA mismatch")
    if raw.get("error") is not None:
        errors.append("candidate error present")
    if raw.get("schema") != "xvfb-xlib-select-buffering-a03-v1":
        errors.append("schema mismatch")
    if expectations.get("schema") != "xvfb-xlib-select-buffering-audit-expectations-v2":
        errors.append("expectations schema mismatch")

    expected_cases = [
        ("select-first", None, True),
        ("same-connection-query-first", "same", False),
        ("separate-query-connection-first", "separate", True),
    ]
    cases = raw.get("cases", [])
    if len(cases) != len(expected_cases):
        errors.append("case count")
    keycode = expectations.get("expected_keycode")
    window = expectations.get("expected_window")
    for case, (name, query_mode, fd_ready) in zip(cases, expected_cases):
        if (case.get("case"), case.get("query_mode")) != (name, query_mode):
            errors.append(name + ": identity/order")
        for edge_name, event_type, state_key in (("press", 2, "keymap_down_seen"),
                                                  ("release", 3, "keymap_up_seen")):
            edge = case.get(edge_name, {})
            if edge.get("fd_select_ready") is not fd_ready:
                errors.append(name + ": " + edge_name + " fd readiness")
            if edge.get("expected_event_found") is not True:
                errors.append(name + ": " + edge_name + " expected event missing")
            if edge.get("expected_type") != event_type:
                errors.append(name + ": " + edge_name + " expected type")
            if edge.get("expected_keycode") != keycode:
                errors.append(name + ": " + edge_name + " expected keycode")
            if edge.get("expected_window") != window:
                errors.append(name + ": " + edge_name + " expected window")
            matches = [event for event in edge.get("events", [])
                       if event.get("type") == event_type
                       and event.get("detail") == keycode
                       and event.get("window") == window]
            if len(matches) != 1:
                errors.append(name + ": " + edge_name + " exact frozen identity cardinality")
            if query_mode is not None and case.get(state_key) is not True:
                errors.append(name + ": " + state_key)
            if query_mode is None and case.get(state_key) is not None:
                errors.append(name + ": unexpected keymap query")
            if query_mode == "same" and edge.get("xlib_pending_before_drain") != 1:
                errors.append(name + ": expected event not already buffered in Xlib")
    if raw.get("xvfb_exit") != 0 or raw.get("xvfb_stopped") is not True:
        errors.append("Xvfb cleanup")
    decision = "PASS_METHOD_SCOPED_WITH_POSTRUN_IDENTITY_BINDING" if not errors else "FAIL"
    return {"schema": "xvfb-xlib-select-buffering-audit-v2",
            "expectations_sha256": hashlib.sha256(
                json.dumps(expectations, sort_keys=True).encode("utf-8")).hexdigest(),
            "source_sha256": probe_sha,
            "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "checked_cases": len(cases), "expected_edges": 6,
            "same_connection_edges_with_fd_not_ready_but_xlib_buffered": sum(
                1 for case in cases if case.get("query_mode") == "same"
                for edge in (case.get("press", {}), case.get("release", {}))
                if edge.get("fd_select_ready") is False and edge.get("xlib_pending_before_drain") == 1),
            "independent_query_connection_edges_fd_ready": sum(
                1 for case in cases if case.get("query_mode") == "separate"
                for edge in (case.get("press", {}), case.get("release", {}))
                if edge.get("fd_select_ready") is True),
            "errors": errors, "decision": decision}


def main():
    raw_bytes = (HERE / "evidence" / "RAW.json").read_bytes()
    raw = json.loads(raw_bytes)
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    expectations = json.loads((HERE / "evidence" / "AUDIT_EXPECTATIONS_V2.json").read_text(encoding="utf-8"))
    report = audit(raw_bytes, raw, freeze, (HERE / "probe.py").read_bytes(), expectations)
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if report["decision"] == "PASS_METHOD_SCOPED_WITH_POSTRUN_IDENTITY_BINDING" else 1)


if __name__ == "__main__":
    main()
