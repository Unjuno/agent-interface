"""Independent raw-result contract audit for diagnostic A03."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
raw = json.loads((HERE / "evidence" / "RAW.json").read_text(encoding="utf-8"))
errors = []
probe_sha = hashlib.sha256((HERE / "probe.py").read_bytes()).hexdigest()
if probe_sha != freeze["probe_sha256"]:
    errors.append("probe SHA mismatch")
if raw.get("source_sha256") != probe_sha:
    errors.append("raw source SHA mismatch")
if raw.get("error") is not None:
    errors.append("candidate error present")
if raw.get("schema") != "xvfb-xlib-select-buffering-a03-v1":
    errors.append("schema mismatch")
expected = [
    ("select-first", None, True),
    ("same-connection-query-first", "same", False),
    ("separate-query-connection-first", "separate", True),
]
cases = raw.get("cases", [])
if len(cases) != len(expected):
    errors.append("case count")
for case, (name, query_mode, fd_ready) in zip(cases, expected):
    if (case.get("case"), case.get("query_mode")) != (name, query_mode):
        errors.append(name + ": identity/order")
    for edge_name, expected_type, state_key in (("press", 2, "keymap_down_seen"),
                                                 ("release", 3, "keymap_up_seen")):
        edge = case.get(edge_name, {})
        if edge.get("fd_select_ready") is not fd_ready:
            errors.append(name + ": " + edge_name + " fd readiness")
        if edge.get("expected_event_found") is not True:
            errors.append(name + ": " + edge_name + " expected event missing")
        matches = [e for e in edge.get("events", [])
                   if e.get("type") == expected_type
                   and e.get("detail") == edge.get("expected_keycode")
                   and e.get("window") == edge.get("expected_window")]
        if len(matches) != 1:
            errors.append(name + ": " + edge_name + " exact event cardinality")
        if query_mode is not None and case.get(state_key) is not True:
            errors.append(name + ": " + state_key)
        if query_mode is None and case.get(state_key) is not None:
            errors.append(name + ": unexpected keymap query")
        if query_mode == "same" and edge.get("xlib_pending_before_drain") != 1:
            errors.append(name + ": expected event not already buffered in Xlib")
if raw.get("xvfb_exit") != 0 or raw.get("xvfb_stopped") is not True:
    errors.append("Xvfb cleanup")
decision = "PASS_METHOD_SCOPED" if not errors else "FAIL"
report = {"schema": "xvfb-xlib-select-buffering-audit-v1",
          "source_sha256": probe_sha,
          "raw_sha256": hashlib.sha256((HERE / "evidence" / "RAW.json").read_bytes()).hexdigest(),
          "checked_cases": len(cases), "expected_edges": 6,
          "same_connection_edges_with_fd_not_ready_but_xlib_buffered": sum(
              1 for c in cases if c.get("query_mode") == "same"
              for edge in (c.get("press", {}), c.get("release", {}))
              if edge.get("fd_select_ready") is False and edge.get("xlib_pending_before_drain") == 1),
          "independent_query_connection_edges_fd_ready": sum(
              1 for c in cases if c.get("query_mode") == "separate"
              for edge in (c.get("press", {}), c.get("release", {}))
              if edge.get("fd_select_ready") is True),
          "errors": errors, "decision": decision}
print(json.dumps(report, sort_keys=True))
raise SystemExit(0 if decision == "PASS_METHOD_SCOPED" else 1)
