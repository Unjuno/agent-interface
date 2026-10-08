"""Independent audit for pinned current-main completion-time backlog cases."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def repo_root():
    for parent in HERE.parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("repository root not found")


def verify_sources(repo=None):
    repo = Path(repo) if repo is not None else repo_root()
    for name, spec in FREEZE["sources"].items():
        data = subprocess.check_output(
            ["git", "-C", str(repo), "show", f"{FREEZE['main_commit']}:{spec['path']}"])
        blob = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse",
             f"{FREEZE['main_commit']}:{spec['path']}"], text=True).strip()
        if blob != spec["git_blob"] or hashlib.sha256(data).hexdigest() != spec["sha256"]:
            raise ValueError(f"frozen source identity mismatch: {name}")


def validate(result, raw, freeze=None, repo=None):
    freeze = FREEZE if freeze is None else freeze
    verify_sources(repo)
    if (result.get("schema") != "issue59-v39-future-done-backlog-result-a03" or
            result.get("status") != "CONSTRUCTION_OBSERVATION" or
            result.get("main_commit") != freeze["main_commit"]):
        raise ValueError("result identity mismatch")
    cases = result.get("cases")
    if not isinstance(cases, list) or [c.get("path") for c in cases] != [
            "queued_terminal", "cancel_needed"]:
        raise ValueError("case set mismatch")
    flattened = [{"case": case["path"], **event}
                 for case in cases for event in case["events"]]
    if flattened != raw:
        raise ValueError("raw event stream mismatch")
    for case in cases:
        admission = case["result"]["admission"]
        if (admission.get("status") != "REJECTED_POLICY_INVALIDATED" or
                admission.get("input_authority_admitted") is not False or
                admission.get("grants_input_authority") is not False):
            raise ValueError("invalidated planner result gained admission")
        events = case["events"]
        kinds = [event.get("event") for event in events]
        if kinds.count("monitor_invalidated") != 1 or kinds.count(
                "planner_result_consumed") != 1:
            raise ValueError("missing invalidation or planner result boundary")
        invalid_at = kinds.index("monitor_invalidated")
        result_at = kinds.index("planner_result_consumed")
        if not invalid_at < result_at:
            raise ValueError("planner result consumed before invalidation")
        observed = next(event for event in events if event["event"] == "monitor_received")
        if observed.get("future_done") is not True:
            raise ValueError("backlog observation was not processed after future completion")
        terminal = case["result"]["current_terminal"]
        if terminal.get("release") != {
                "verified": True, "keys_down": [], "buttons_down": []}:
            raise ValueError("terminal did not verify empty release")
        if case["path"] == "queued_terminal":
            if (terminal.get("status") != "completed" or
                    "executor_cancel_write" in kinds or
                    kinds.index("terminal_dequeued") > result_at):
                raise ValueError("queued terminal path mismatch")
        else:
            required = ["executor_cancel_write", "executor_cancel_flush",
                        "planner_interrupt_transport", "terminal_dequeued"]
            positions = [kinds.index(event) for event in required]
            if positions != sorted(positions) or terminal.get("status") != "cancelled":
                raise ValueError("cancel-needed path order/status mismatch")
    return True


def main():
    result_path = HERE / "RESULT.json"
    events_path = HERE / "events.jsonl"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    raw = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
    validate(result, raw)
    audit = {
        "schema": "issue59-v39-future-done-backlog-audit-v1",
        "status": "PASS_BACKLOG_INVALIDATION",
        "frozen_main": FREEZE["main_commit"],
        "event_rows": len(raw),
        "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        "events_sha256": hashlib.sha256(events_path.read_bytes()).hexdigest(),
        "checks": {"frozen_sources": True,
                   "queued_terminal_and_invalidation_retained": True,
                   "cancel_needed_path_closes_empty_before_result": True,
                   "both_final_admissions_rejected": True},
    }
    output = HERE / "AUDIT.json"
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    output.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8",
                      newline="\n")
    print(json.dumps(audit, separators=(",", ":")))


if __name__ == "__main__":
    main()
