"""Replay retained typed MAP01 events through the frozen current-main V39 monitor."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
LOCK = json.loads((HERE / "SOURCE_LOCK.json").read_text(encoding="utf-8"))
RESULT_DIR = REPO / "research/doom/results/map01-v39-coast-liveness-live-01"
CONTROLLER_PATH = REPO / "research/doom/map01_overlap_controller_v39.py"
GUARD_PATH = REPO / "research/live_control/observable_signal_guard_v2.py"
sys.path[:0] = [str(CONTROLLER_PATH.parent), str(GUARD_PATH.parent),
                str(REPO / "research/live_control")]
import map01_overlap_controller_v39 as controller


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git_head():
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, check=True,
        capture_output=True, text=True).stdout.strip()


def require_source_lock():
    if git_head() != LOCK["source_main"]:
        raise SystemExit("worktree HEAD differs from SOURCE_LOCK")
    for relative, expected in LOCK["current_runtime_sources"].items():
        if sha256(REPO / relative) != expected:
            raise SystemExit(f"current runtime source mismatch: {relative}")
    for relative, expected in LOCK["historical_inputs"].items():
        if sha256(REPO / relative) != expected:
            raise SystemExit(f"historical input mismatch: {relative}")


class RecordedSignalReader:
    def __init__(self, signal):
        self.signal = signal

    def read(self, _observation):
        return self.signal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite output: {output}")
    require_source_lock()

    report_path = RESULT_DIR / "report.json"
    events_path = RESULT_DIR / "runtime/events.jsonl"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
    typed = {row["sequence"]: row for row in rows
             if row.get("event") == "typed_observation" and
             type(row.get("sequence")) is int and 166 <= row["sequence"] <= 218}
    if sorted(typed) != list(range(166, 219)):
        raise SystemExit("expected consecutive exact typed source/trigger rows 166..218")

    decision = report["decisions"][5]
    source = typed[166]
    validity = decision["cover_validity_admission"]["authored"]
    requires_ammo = controller.cover_requires_ammo(decision["cover_policy"])
    monitor, admission = controller.build_cover_monitor(
        RecordedSignalReader(source["signals"]["health"]), source, validity, 5,
        ammo_reader=RecordedSignalReader(source["signals"]["ammo"]),
        requires_ammo=requires_ammo)
    if (admission["status"] != "admitted" or
            admission.get("monitor_mode") != "paired_health_ammo" or
            admission.get("grants_input_authority") is not False):
        raise SystemExit("current paired monitor did not admit the exact recorded source pair")

    trace = []
    first_invalidation = None
    for sequence in range(167, 219):
        event = typed[sequence]
        outcome = monitor.observe(event)
        row = {
            "sequence": sequence,
            "health": event["signals"]["health"]["value"],
            "ammo": event["signals"]["ammo"]["value"],
            "returned_invalidation": outcome is not None,
        }
        if outcome is not None:
            row["reason"] = outcome["reason"]
            row["outcomes"] = {
                signal: result["status"] + ":" + result["reason"]
                for signal, result in outcome.get("outcomes", {}).items()
            }
            row["requires_new_decision"] = outcome["requires_new_decision"]
            row["grants_input_authority"] = outcome["grants_input_authority"]
            first_invalidation = row
        trace.append(row)
        if outcome is not None:
            break

    historical_invalidation = decision["policy_invalidation"]
    terminal_observed_ns = decision["planner_terminal_observed_ns"]
    evaluated_ns = historical_invalidation["outcome_evaluated_ns"]
    historical_turn = {
        "status": decision["planner_turn_status"],
        "answer_eligible": decision["planner_answer_eligible"],
        "answer_discarded": decision["model_action_discarded"],
        "model_turn_ms": decision["model_ns"] / 1e6,
        "invalidation_evaluation_to_interrupted_terminal_ms":
            (terminal_observed_ns - evaluated_ns) / 1e6,
        "natural_answer_return_observed": False,
    }
    result = {
        "schema": "v39-current-main-paired-guard-replay-result-v1",
        "result_kind": "posthoc deterministic replay over retained live-run typed events",
        "source_main": LOCK["source_main"],
        "current_runtime_source_sha256": LOCK["current_runtime_sources"],
        "historical_source_commit": LOCK["historical_source_commit"],
        "historical_controller_sha256": LOCK["historical_controller_sha256"],
        "historical_inputs_sha256": LOCK["historical_inputs"],
        "source": {
            "sequence": 166,
            "health": source["signals"]["health"]["value"],
            "ammo": source["signals"]["ammo"]["value"],
        },
        "authored_validity": validity,
        "current_monitor_admission": {
            "status": admission["status"],
            "monitor_mode": admission["monitor_mode"],
            "hard_health_minimum": admission["effective"]["hard_minimum"],
            "hard_ammo_minimum": 1,
            "requires_ammo": requires_ammo,
            "grants_input_authority": admission["grants_input_authority"],
        },
        "replayed_rows": len(trace),
        "boundary_row_200": next(row for row in trace if row["sequence"] == 200),
        "first_invalidation": first_invalidation,
        "historical_live_turn": historical_turn,
        "trace": trace,
        "scope_limit": (
            "This replays the exact retained typed health/ammo rows through the current "
            "monitor only. It does not execute the current live capture/session/interrupt/"
            "release path, establish task effect or recovery, or replace a fresh assigned live run."
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "replayed_rows": len(trace),
                      "first_invalidation": first_invalidation,
                      "current_main": LOCK["source_main"]}, indent=2))


if __name__ == "__main__":
    main()
