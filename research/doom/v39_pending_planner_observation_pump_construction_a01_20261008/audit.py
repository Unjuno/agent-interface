"""Independent raw/result audit for the synthetic pending-pump construction."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
REPOSITORY = PACKAGE.parents[2]
RESULT_KEYS = {
    "status", "schema", "main_commit", "controller_git_blob", "controller_sha256",
    "synthetic_event_stream_sha256", "source_composition_executed",
    "observation_processed_while_planner_pending", "invalidation_reason",
    "planner_interrupt_status", "cancel_command", "terminal_status", "release",
    "cover_renewals", "planner_worker_body_calls", "trace", "scope",
}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _git_blob_sha1(raw: bytes) -> str:
    header = b"blob " + str(len(raw)).encode("ascii") + b"\0"
    return hashlib.sha1(header + raw).hexdigest()


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _independent_expected(package: Path) -> tuple[dict, list[str]]:
    freeze = _json(package / "FREEZE.json")
    source = (REPOSITORY / freeze["controller_path"]).read_bytes()
    events_raw = (package / "inputs/events.json").read_bytes()
    events = json.loads(events_raw)
    if _sha(source) != freeze["controller_sha256"]:
        raise ValueError("frozen controller source changed")
    if _git_blob_sha1(source) != freeze["controller_git_blob"]:
        raise ValueError("controller Git blob identity mismatch")
    if _sha(events_raw) != freeze["events_sha256"]:
        raise ValueError("synthetic raw stream changed")
    if events.get("schema") != "v39-pending-pump-synthetic-events-v1":
        raise ValueError("unexpected synthetic event schema")
    rows = events.get("rows")
    if (events.get("time_domain") != "synthetic_order_only" or
            not isinstance(rows, list) or len(rows) != 2 or
            any(row.get("synthetic") is not True for row in rows)):
        raise ValueError("synthetic event contract mismatch")
    observation, terminal = rows
    if observation.get("event") != "typed_observation" or terminal.get("event") != "terminal":
        raise ValueError("event order mismatch")
    if terminal.get("id") != "cover-0":
        raise ValueError("terminal identity mismatch")
    safe_release = {"verified": True, "keys_down": [], "buttons_down": []}
    if terminal.get("status") != "cancelled" or terminal.get("release") != safe_release:
        raise ValueError("synthetic terminal is not the declared neutral cancellation")

    # This expected object is independently assembled from the frozen source
    # identity, synthetic input, and trace relations below; it does not import
    # or call candidate.run_probe().
    return ({
        "status": "PASS_SYNTHETIC_PENDING_PUMP_RELEASE_ORDER",
        "schema": "v39-pending-pump-construction-result-v1",
        "main_commit": freeze["main_commit"],
        "controller_git_blob": freeze["controller_git_blob"],
        "controller_sha256": _sha(source),
        "synthetic_event_stream_sha256": freeze["events_sha256"],
        "source_composition_executed": [
            "nested wait() event dispatcher",
            "pending planner ThreadPoolExecutor block",
            "cancel_invalidated_cover()",
        ],
        "observation_processed_while_planner_pending": True,
        "invalidation_reason": "synthetic_policy_invalidation",
        "planner_interrupt_status": "interrupted",
        "cancel_command": {"op": "cancel", "id": "cover-0"},
        "terminal_status": "cancelled",
        "release": safe_release,
        "cover_renewals": 0,
        "planner_worker_body_calls": 0,
        "trace": [
            {"event": "future_done_check", "done": False},
            {"event": "executor_event_dequeued", "row_event": observation["event"]},
            {"event": "future_done_check", "done": False},
            {"event": "typed_observation_monitored", "future_pending": True,
             "sequence": observation["sequence"]},
            {"event": "planner_interrupt_entered", "future_pending": True},
            {"event": "executor_command_written",
             "command": {"op": "cancel", "id": terminal["id"]}},
            {"event": "planner_interrupt_transport_sent"},
            {"event": "executor_event_dequeued", "row_event": terminal["event"]},
            {"event": "cleanup_stage", "stage": "planner_result_validation"},
        ],
        "scope": [
            "The production AST block ran with synthetic executor rows and a fake pending future.",
            "FakePool does not start a worker or run planner.await_turn; this is not a real concurrency or planner-latency test.",
            "No game, model, GUI, OS input, physical key state, useful feedback, recovery, or task effect was exercised.",
        ],
    }, [observation, terminal])


def audit_result(result: dict, package: Path = PACKAGE) -> dict:
    failures = []
    rows = None
    try:
        freeze = _json(package / "FREEZE.json")
        expected, rows = _independent_expected(package)
        if freeze.get("schema") != "v39-pending-pump-freeze-v1":
            failures.append("freeze_schema")
        if set(result) != RESULT_KEYS or result != expected:
            failures.append("result_matches_reconstruction")

        trace = result.get("trace") if isinstance(result, dict) else None
        if not isinstance(trace, list) or not isinstance(rows, list) or len(rows) != 2:
            failures.append("trace_shape")
        else:
            monitor = next((i for i, item in enumerate(trace)
                            if item.get("event") == "typed_observation_monitored"), None)
            interrupt = next((i for i, item in enumerate(trace)
                              if item.get("event") == "planner_interrupt_entered"), None)
            cancel = next((i for i, item in enumerate(trace)
                           if item.get("event") == "executor_command_written"), None)
            transport = next((i for i, item in enumerate(trace)
                              if item.get("event") == "planner_interrupt_transport_sent"), None)
            terminal = next((i for i, item in enumerate(trace)
                             if item.get("event") == "executor_event_dequeued" and
                             item.get("row_event") == rows[1]["event"]), None)
            if not (monitor is not None and interrupt is not None and cancel is not None and
                    transport is not None and terminal is not None and
                    monitor < interrupt < cancel < transport < terminal and
                    trace[monitor].get("future_pending") is True and
                    trace[interrupt].get("future_pending") is True and
                    trace[cancel].get("command") == expected["cancel_command"]):
                failures.append("pending_observation_cancel_terminal_order")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        failures.append("frozen_inputs_reconstruct")

    checks_total = 4
    return {
        "schema": "v39-pending-pump-construction-audit-v1",
        "status": "PASS_SOURCE_COMPOSITION" if not failures else "FAIL_SOURCE_COMPOSITION",
        "checks_passed": max(0, checks_total - len(failures)),
        "checks_total": checks_total,
        "failed_checks": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, default=PACKAGE / "RESULT.json")
    parser.add_argument("--output", type=Path, default=PACKAGE / "AUDIT.json")
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"refusing to overwrite existing output: {args.output}")
    audit = audit_result(_json(args.result))
    args.output.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
