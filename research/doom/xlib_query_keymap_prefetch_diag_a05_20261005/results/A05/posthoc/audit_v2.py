"""Posthoc raw-only audit V2; binds the key identity to frozen protocol `a`."""
EXPECTED_KEYCODE = 38  # keysym `a` in the pinned Ubuntu/Xvfb fixture
EXPECTED_SCHEMA = "xlib-query-keymap-prefetch-a05-v1"
EXPECTED_ALLOCATION = "MAP01-V39-XLIB-QUERY-PREFETCH-A05-20261005-02"


def audit(raw):
    edges = raw.get("edges")
    checks = {
        "schema": raw.get("schema") == EXPECTED_SCHEMA,
        "allocation": raw.get("allocation_id") == EXPECTED_ALLOCATION,
        "one_candidate": raw.get("candidate_invocations") == 1,
        "complete": raw.get("candidate_complete") is True,
        "protocol_keycode_a": raw.get("fixture", {}).get("keycode") == EXPECTED_KEYCODE,
        "focus_matches_window": raw.get("fixture", {}).get("focus_id") == raw.get("fixture", {}).get("window_id"),
        "clean_xvfb": raw.get("cleanup", {}).get("xvfb_stopped") is True
            and raw.get("cleanup", {}).get("xvfb_exit") == 0,
        "two_edges": isinstance(edges, list) and len(edges) == 2,
    }
    if isinstance(edges, list) and len(edges) == 2:
        checks["edge_order"] = [e.get("label") for e in edges] == ["down", "up"]
        checks["keymap_sequence"] = [e.get("observed_key_down") for e in edges] == [True, False]
        checks["clock_order"] = all(
            type(e.get("inject_started_ns")) is int
            and e["inject_started_ns"] <= e.get("inject_synced_ns", -1)
            <= e.get("query_reply_returned_ns", -1) for e in edges)
        checks["separate_edge_clocks"] = edges[0].get("query_reply_returned_ns", 0) < edges[1].get("inject_started_ns", 0)
        checks["exact_protocol_edges"] = all(
            e.get("expected_key_down") is down
            and e.get("matched_event", {}).get("type") == kind
            and e.get("matched_event", {}).get("detail") == EXPECTED_KEYCODE
            and e.get("matched_event", {}).get("window_id") == raw.get("fixture", {}).get("window_id")
            and e.get("matched_event", {}).get("matches") is True
            for e, down, kind in zip(edges, (True, False), (2, 3)))
        checks["preselect_target"] = all(
            e.get("target_prefetched_before_select") is True
            and any(row.get("matches") is True and row.get("detail") == EXPECTED_KEYCODE
                    and row.get("type") == kind
                    and row.get("window_id") == raw.get("fixture", {}).get("window_id")
                    for row in e.get("queued_snapshot_before_select", []))
            for e, kind in zip(edges, (2, 3)))
        checks["socket_not_readable"] = all(e.get("socket_readable_after_queue_check") is False for e in edges)
        checks["noise_preserved"] = all(isinstance(e.get("event_rows"), list) for e in edges)
    else:
        for key in ("edge_order", "keymap_sequence", "clock_order", "separate_edge_clocks",
                    "exact_protocol_edges", "preselect_target", "socket_not_readable", "noise_preserved"):
            checks[key] = False
    return {"status": "PASS_SOURCE_PINNED_QUEUE_PREFETCH" if all(checks.values()) else "FAIL",
            "checks": checks}
