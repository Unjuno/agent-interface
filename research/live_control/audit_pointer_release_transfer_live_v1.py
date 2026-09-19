"""Independent audit for the frozen actual pointer release transfer."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PREREG = HERE / "pointer_release_transfer_live_v1_prereg.json"
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    plan = read(PREREG); root = REPO / plan["output"]
    report, events, owners = (read(root / "report.json"), read(root / "events.json"),
                              read(root / "owner-events.json"))
    released = [row for row in events if row.get("event") == "input_released"]
    terminals = [row for row in events if row.get("event") == "terminal"]
    moves = [row for row in events if row.get("event") == "pointer_admission" and
             row.get("operation") == "move"]
    checks = {
        "frozen_sources": all(sha(REPO / name) == digest
                              for name, digest in plan["source_sha256"].items()),
        "allocation": report["allocation_id"] == plan["allocation_id"],
        "one_release_terminal": len(released) == len(terminals) == 1,
        "report_all_pass": report["passed"] is True and all(report["checks"].values()),
        "event_order": events.index(released[0]) < events.index(terminals[0]),
        "owner_identity": released[0]["owner_release"] in owners and
            released[0]["intent_token"] == report["accepted"]["intent_token"],
        "focus_cause": released[0]["owner_release"]["reason"] == "focus_changed" and
            terminals[0]["decision_reason"] == "focus_changed",
        "empty_release": released[0]["owner_release"]["verified"] is True and
            released[0]["owner_release"]["buttons_down"] == [] and
            terminals[0]["release"]["verified"] is True,
        "one_initial_move_no_tail": len(moves) == 1 and moves[0]["payload"] == plan["points"][0],
        "zero_cancel_model_retry": not any(row.get("event") == "cancel_requested" for row in events) and
            report["model_calls"] == report["retry_count"] == 0,
        "thresholds": report["metrics_ms"]["focus_request_to_physical_release_ms"] <= 50 and
            report["metrics_ms"]["focus_request_to_release_publication_ms"] <= 75 and
            report["metrics_ms"]["focus_request_to_terminal_ms"] <= 150,
    }
    audit = {"passed": all(checks.values()), "checks": checks,
             "metrics_ms": report["metrics_ms"], "events": len(events),
             "owner_records": len(owners), "scope": plan["scope"]}
    (root / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2)); return 0 if audit["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
