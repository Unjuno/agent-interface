"""Independent standard-library audit of the frozen C03 raw output."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PASS = "PASS_C03_POST_SAMPLE_CANCEL_BOUNDARY_REPRODUCED"
FAIL = "FAIL_C03_EXPECTED_BOUNDARY_NOT_REPRODUCED"
STOP = "STOP_C03_EVIDENCE_OR_CUSTODY_INCOMPLETE"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit():
    raw = json.loads((HERE / "candidate.raw.json").read_text(encoding="utf-8"))
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    checks = {}
    checks["raw_source_hashes_match_freeze"] = all(
        sha(HERE / "dependencies" / name) == digest
        for name, digest in freeze["source_sha256"].items())
    checks["raw_embedded_source_hashes_match_freeze"] = raw.get("source_sha256") == {
        label: freeze["source_sha256"][name]
        for label, name in (("main_v10", "input_owner_v10.py"),
                            ("pr7440_v12", "input_owner_v12.py"))}
    checks["candidate_hash_matches_freeze"] = sha(HERE / "candidate.py") == freeze["candidate_sha256"]
    rows = {row["source"]: row for row in raw["cases"]}
    expected_rows = {"main_v10_dequeue_cancel", "pr7440_v12_post_sample_cancel",
                     "pr7440_v12_ordinary_control"}
    checks["exact_three_named_cases"] = set(rows) == expected_rows
    if checks["exact_three_named_cases"]:
        for name, row in rows.items():
            events = row["key_events"]
            checks[name + "_one_press_one_release"] = (
                len(events) == 2
                and [event["event"] for event in events] == [2, 3]
                and [event["keycode"] for event in events] == [38, 38]
                and events[0]["at_ns"] < events[1]["at_ns"])
            checks[name + "_verified_empty_release"] = (
                row["release_reply_verified"] is True
                and row["owner_receipt"]["verified"] is True
                and row["owner_receipt"]["keys_down"] == [])
            checks[name + "_canceller_settled"] = row["canceller_thread_finished"] is True
        main = rows["main_v10_dequeue_cancel"]
        candidate = rows["pr7440_v12_post_sample_cancel"]
        ordinary = rows["pr7440_v12_ordinary_control"]
        checks["main_cancel_after_dequeue_before_keyup"] = (
            type(main["dequeued_ns"]) is int
            and type(main["cancel_visible_ns"]) is int
            and main["dequeued_ns"] <= main["cancel_visible_ns"] < main["key_events"][-1]["at_ns"]
            and main["cancel_state_after_release"] is True)
        checks["v12_cancel_after_false_sample_before_keyup"] = (
            type(candidate["dequeued_ns"]) is int
            and type(candidate["cancel_sample_false_ns"]) is int
            and type(candidate["cancel_visible_ns"]) is int
            and candidate["dequeued_ns"] <= candidate["cancel_armed_after_dequeue_ns"]
            < candidate["cancel_sample_false_ns"] < candidate["cancel_visible_ns"]
            < candidate["key_events"][-1]["at_ns"]
            and candidate["cancel_state_after_release"] is True)
        checks["v12_ordinary_positive_control"] = (
            ordinary["cancel_state_after_release"] is False
            and ordinary["cancel_sample_false_ns"] is None
            and ordinary["owner_receipt"]["reason"] == "release")
        checks["main_retains_ordinary_cause"] = main["owner_receipt"]["reason"] == "release"
        checks["v12_loses_post_sample_cancel_cause"] = candidate["owner_receipt"]["reason"] == "release"
    else:
        checks["main_retains_ordinary_cause"] = False
        checks["v12_loses_post_sample_cancel_cause"] = False
    structural = all(value for key, value in checks.items()
                     if key != "v12_loses_post_sample_cancel_cause")
    reproduced = structural and checks["v12_loses_post_sample_cancel_cause"]
    report = {
        "schema": "map01-v39-cancel-release-cause-c03-audit-v1",
        "gate": PASS if reproduced else FAIL if structural else STOP,
        "checks": checks,
        "failed_checks": sorted(key for key, value in checks.items() if not value),
        "scope": "one deterministic fake-Xlib owner-thread schedule per source",
        "raw_sha256": sha(HERE / "candidate.raw.json"),
        "candidate_sha256": sha(HERE / "candidate.py"),
        "auditor_sha256": sha(Path(__file__)),
    }
    (HERE / "AUDIT.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                                     encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if reproduced else 1


if __name__ == "__main__":
    raise SystemExit(audit())
