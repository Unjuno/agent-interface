"""Independent raw-only audit for the one-shot Xlib queue diagnostic."""
import argparse
import json
from pathlib import Path

# X11 core event codes are fixed by the protocol: KeyPress=2, KeyRelease=3.

def audit(raw):
    edges = raw.get("edges")
    checks = {
        "schema": raw.get("schema") == "xlib-query-keymap-prefetch-a05-v1",
        "allocation": raw.get("allocation_id") == "MAP01-V39-XLIB-QUERY-PREFETCH-A05-20261005-02",
        "one_invocation": raw.get("candidate_invocations") == 1,
        "candidate_complete": raw.get("candidate_complete") is True,
        "two_edges": isinstance(edges, list) and len(edges) == 2,
        "clean_xvfb": (raw.get("cleanup", {}).get("xvfb_stopped") is True
                        and raw.get("cleanup", {}).get("xvfb_exit") == 0),
    }
    if isinstance(edges, list) and len(edges) == 2:
        checks["edge_labels"] = [e.get("label") for e in edges] == ["down", "up"]
        checks["keymap_sequence"] = [e.get("observed_key_down") for e in edges] == [True, False]
        checks["queue_prefetched"] = all(type(e.get("queued_before_select")) is int and e["queued_before_select"] >= 1 for e in edges)
        checks["target_prefetched_before_select"] = all(
            e.get("target_prefetched_before_select") is True
            and isinstance(e.get("queued_snapshot_before_select"), list)
            and any(row.get("matches") is True for row in e["queued_snapshot_before_select"])
            for e in edges)
        checks["socket_not_readable"] = all(e.get("socket_readable_after_queue_check") is False for e in edges)
        checks["event_rows_preserved"] = all(isinstance(e.get("event_rows"), list) for e in edges)
        checks["pending_queue_retained"] = all(type(e.get("pending_events_after_collection")) is int and e["pending_events_after_collection"] >= 0 for e in edges)
        expected = [2, 3]
        checks["exact_client_events"] = all(
            e.get("matched_event", {}).get("matches") is True
            and e["matched_event"].get("type") == kind
            and e["matched_event"].get("window_id") == raw.get("fixture", {}).get("window_id")
            and e["matched_event"].get("detail") == raw.get("fixture", {}).get("keycode")
            for e, kind in zip(edges, expected)
        )
        checks["ordered_clocks"] = all(
            type(e.get("inject_started_ns")) is int
            and e["inject_started_ns"] <= e.get("inject_synced_ns", -1)
            <= e.get("query_reply_returned_ns", -1)
            for e in edges
        )
        checks["edge_clock_order"] = edges[0].get("query_reply_returned_ns", 0) < edges[1].get("inject_started_ns", 0)
    else:
        for name in ("edge_labels", "keymap_sequence", "queue_prefetched", "target_prefetched_before_select", "socket_not_readable", "event_rows_preserved", "pending_queue_retained", "exact_client_events", "ordered_clocks", "edge_clock_order"):
            checks[name] = False
    return {"status": "PASS_QUEUE_PREFETCH_DIAGNOSTIC" if all(checks.values()) else "FAIL", "checks": checks}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--raw", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    result = audit(json.loads(Path(a.raw).read_text()))
    Path(a.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_QUEUE_PREFETCH_DIAGNOSTIC" else 1)
