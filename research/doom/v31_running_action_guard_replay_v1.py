"""Replay running-action validity on retained v31 exact program observations."""
import copy
import hashlib
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LIVE = HERE.parent / "live_control"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(LIVE))
from doom_action_snapshot_v1 import build_action_snapshot
from doom_hud_signal_v2 import DoomStatusNumberReader
from running_action_guard_v1 import CANCEL, COMPLETED, REVOKED, RunningActionGuard


ROOT = HERE / "results/map01-soft-context-v31-live-01"
CONSTRUCTION = HERE / "results/v31-action-health-ammo-replay-v2/audit.json"
WAD = REPO / "_vizdoom/vizdoom/freedoom2.wad"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run():
    report = read(ROOT / "report.json")
    construction = read(CONSTRUCTION)
    events = [json.loads(line) for line in
              (ROOT / "runtime/events.jsonl").read_text(encoding="utf-8").splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    terminals = {row["id"]: row for row in events if row.get("event") == "terminal"}
    resolver = lambda value: ROOT / "runtime" / Path(value).name
    all_readers = {
        signal_id: DoomStatusNumberReader(
            WAD, signal_id=signal_id, image_resolver=resolver)
        for signal_id in ("health", "ammo")}
    rows = []
    for source in construction["historical_rows"]:
        iteration = source["iteration"]
        decision = report["decisions"][iteration]
        trace = decision["execution_trace"]
        if len(trace) != 1:
            raise AssertionError("retained v31 replay expects one primary program per decision")
        execution = trace[0]
        action = source["commands"]
        initial = source["result"]
        contract = initial["contract"]
        readers = {name: all_readers[name] for name in contract["source"]["signals"]}
        guard = RunningActionGuard(action, contract, initial)
        guard.admit_program({"event": "accepted", "id": execution["id"],
                             "accepted_ns": execution["accepted_ns"]})
        frames = [row for row in observations
                  if row.get("id") == execution["id"] and
                  execution["accepted_ns"] <= row["capture_ns"] <= execution["terminal_ns"]]
        values = []
        for observation in frames:
            snapshot = build_action_snapshot(observation, contract, readers)
            receipt = guard.check_current(snapshot, observation["emit_ns"])
            if receipt["state"] == CANCEL:
                raise AssertionError("historical primary unexpectedly invalidated")
            values.append({name: signal["value"] for name, signal in snapshot["signals"].items()})
        receipt = guard.record_completed_terminal(terminals[execution["id"]], final=True)
        if receipt["state"] != COMPLETED:
            raise AssertionError("historical program did not close cleanly")
        rows.append({"iteration": iteration, "action": action,
                     "program_id": execution["id"], "exact_frames": len(frames),
                     "signal_values": values, "final_state": receipt["state"],
                     "validity_checks": len(receipt["validity_checks"]),
                     "physical_release_verified": receipt["physical_release_verified"]})

    def injected(kind):
        source = construction["historical_rows"][0]
        if kind == "ammo":
            source = construction["historical_rows"][1]
        action, initial = source["commands"], source["result"]
        guard = RunningActionGuard(action, initial["contract"], initial)
        accepted_ns = initial["controller_decided_ns"] + 1
        identifier = f"injected-{kind}"
        guard.admit_program({"event": "accepted", "id": identifier,
                             "accepted_ns": accepted_ns})
        snapshot = copy.deepcopy(initial["snapshot"])
        snapshot["sequence"] += 1
        snapshot["capture_ns"] += 1
        if kind == "health":
            source_health = initial["contract"]["source"]["signals"]["health"]["value"]
            allowed = next(row["value"] for row in initial["contract"]["predicates"]
                           if row["signal_id"] == "health" and
                           row["operator"] == "max_decrease_from_source")
            snapshot["signals"]["health"]["value"] = source_health - allowed - 1
        else:
            snapshot["signals"]["ammo"]["value"] = 0
        decided_ns = max(accepted_ns + 1, snapshot["capture_ns"] + 1)
        receipt = guard.check_current(snapshot, decided_ns)
        if receipt["state"] != CANCEL:
            raise AssertionError("injected breach did not require cancellation")
        requested_ns = decided_ns + 1
        guard.record_cancel_requested({"event": "cancel_requested", "id": identifier,
                                       "matched": True, "requested_ns": requested_ns})
        receipt = guard.record_cancelled_terminal({
            "event": "terminal", "id": identifier, "status": "cancelled",
            "terminal_ns": requested_ns + 2,
            "release": {"verified": True, "keys_down": [], "buttons_down": [],
                        "verified_ns": requested_ns + 1}})
        return {"kind": kind, "invalidation_reason":
                receipt["invalidation"]["result"]["reason"],
                "final_state": receipt["state"],
                "physical_release_verified": receipt["physical_release_verified"]}

    controls = [injected("health"), injected("ammo")]
    exact_frames = sum(row["exact_frames"] for row in rows)
    return {
        "schema": "v31-running-action-guard-replay-v1",
        "passed": len(rows) == 5 and exact_frames == 22 and
                  all(row["final_state"] == COMPLETED and
                      row["physical_release_verified"] for row in rows) and
                  all(row["final_state"] == REVOKED and
                      row["physical_release_verified"] for row in controls),
        "historical_programs": rows,
        "historical_program_count": len(rows),
        "historical_exact_running_frames": exact_frames,
        "historical_invalidations": 0,
        "injected_controls": controls,
        "model_calls": 0,
        "input_operations": 0,
        "sources": {
            "v31_report": sha(ROOT / "report.json"),
            "v31_runtime_events": sha(ROOT / "runtime/events.jsonl"),
            "action_validity_construction": sha(CONSTRUCTION),
            "running_guard": sha(LIVE / "running_action_guard_v1.py"),
            "doom_snapshot_adapter": sha(HERE / "doom_action_snapshot_v1.py")},
        "finding": "existing per-hold observations can enforce the same exact action contract without another model or capture boundary",
        "limits": "retained-trace counterfactual plus synthetic breaches; no historical cancellation, live latency, gameplay, planner-authored schema-v6 output, survival or completion gain",
    }


def main():
    result = run()
    target = HERE / "results/v31-running-action-guard-replay-v1"
    target.mkdir(parents=True, exist_ok=True)
    (target / "audit.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({key: result[key] for key in (
        "passed", "historical_program_count", "historical_exact_running_frames",
        "historical_invalidations")}, separators=(",", ":")))


if __name__ == "__main__":
    main()
