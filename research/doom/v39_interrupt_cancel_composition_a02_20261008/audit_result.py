"""Independent raw-data auditor for the one-shot composition probe."""
import json
import sys
from pathlib import Path


ALLOWED = {"cancelled", "completed", "expired"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit_case(row):
    events = row["events"]
    kinds = [event["event"] for event in events]
    require(kinds.count("planner_interrupt") == 1, "must send one planner interrupt")
    require(kinds.count("cover_cancel") == 1, "must send one cover cancel")
    interrupt = next(event for event in events if event["event"] == "planner_interrupt")
    cancel = next(event for event in events if event["event"] == "cover_cancel")
    require(interrupt["thread_id"] == "thread-1" and interrupt["turn_id"] == "turn-1",
            "interrupt must identify active turn")
    require(cancel == {"event": "cover_cancel", "op": "cancel", "id": "cover-1"},
            "cover cancel identity mismatch")
    require(kinds.index("planner_interrupt") < kinds.index("cover_cancel") <
            kinds.index("cover_terminal"), "interrupt/cancel/terminal order mismatch")
    term = next(event for event in events if event["event"] == "cover_terminal")
    release = term.get("release")
    neutral = (type(release) is dict and release.get("verified") is True and
               release.get("keys_down") == [] and release.get("buttons_down") == [])
    accepted = term.get("status") in ALLOWED and neutral
    require((row["disposition"] == "accepted") == accepted,
            "terminal acceptance does not match independent policy")
    require(row["expected_accept"] == accepted, "frozen expected disposition mismatch")
    outcome = "request_error" if row["interrupt_fails"] else "requested"
    require(row["interrupt_outcome"] == outcome, "interrupt failure disposition mismatch")
    old = next(event for event in events if event["event"] == "old_turn_result")
    require(old["answer_eligible"] is False and old["answer"] is None,
            "invalidated old answer was admitted")
    require(row["old_answer_eligible"] is False and row["old_answer"] is None,
            "candidate summary admits old answer")
    fresh_rows = [event for event in events if event["event"] == "fresh_turn_result"]
    if row["expected_accept"]:
        require(len(fresh_rows) == 1, "eligible path must produce one fresh turn")
        fresh = fresh_rows[0]
        require(fresh["thread_id"] == "thread-1" and fresh["answer_eligible"] is True and
                fresh["answer"] == {"action": "fresh"}, "fresh turn must not inherit stale answer")
        require([event["input"] for event in events if event["event"] == "turn_started"] ==
                ["old observation", "fresh observation"], "fresh observation order mismatch")
    else:
        require(not fresh_rows, "rejected terminal must not proceed to fresh turn")
    return 1


def main(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    require(data["format"] == "v39-interrupt-cancel-composition-a02-v1", "format mismatch")
    require(data["source_main"] == "f72cd82d62c9d9f3860d4fa40980c56618bf5aaf", "source freeze mismatch")
    require(len(data["cases"]) == 10, "case count mismatch")
    checks = sum(audit_case(row) for row in data["cases"])
    require(checks == 10, "case accounting mismatch")
    print(f"PASS: independently reconstructed {checks}/10 cases; 6/6 invalid terminals refused; stale turn rejected; fresh turn isolated")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_result.py candidate.json")
    try:
        main(sys.argv[1])
    except Exception as error:
        print(f"FAIL: {type(error).__name__}: {error}")
        raise SystemExit(1)
