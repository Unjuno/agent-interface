"""Retain the first pre-input stale failure without rerunning its allocation."""
import hashlib
import json
from pathlib import Path
import shutil
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LIVE = HERE.parent / "live_control"
sys.path[:0] = [str(HERE), str(LIVE)]
from action_validity_admission_v1 import evaluate_action_validity
from doom_action_snapshot_v1 import build_action_snapshot
from doom_action_validity_contract_v1 import build_contract
from doom_hud_signal_v2 import DoomStatusNumberReader


SOURCE = REPO / "results-local/doom/map01-running-action-cancel-live-01"
TARGET = HERE / "results/map01-running-action-cancel-live-01"
PREREG = HERE / "map01_running_action_cancel_live_v1_prereg.json"
DECIDED_NS_FROM_RETAINED_EXCEPTION = 33923450236942


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if TARGET.exists(): raise FileExistsError(TARGET)
    plan = read(PREREG); events_path = SOURCE / "runtime/events.jsonl"
    events = [json.loads(line) for line in events_path.read_text().splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    if len(observations) != 1: raise AssertionError("exactly one pre-input observation expected")
    observation = observations[0]
    wad = REPO / "_vizdoom/vizdoom/freedoom2.wad"
    resolver = lambda value: SOURCE / "runtime" / Path(value).name
    health_reader = DoomStatusNumberReader(wad, signal_id="health", image_resolver=resolver)
    ammo_reader = DoomStatusNumberReader(wad, signal_id="ammo", image_resolver=resolver)
    health, ammo = health_reader.read(observation), ammo_reader.read(observation)
    action = plan["action"]
    authored = {"critical_health_minimum": 1, "maximum_health_loss": 20,
                "minimum_ammo": ammo["value"], "max_current_age_ms": 500}
    contract = build_contract(action, authored, health, ammo)
    snapshot = build_action_snapshot(
        observation, contract, {"health": health_reader, "ammo": ammo_reader})
    result = evaluate_action_validity(
        action, contract, snapshot, DECIDED_NS_FROM_RETAINED_EXCEPTION)
    failure = {
        "allocation_id": plan["allocation_id"],
        "disposition": "RETAIN_PRE_INPUT_STALE_FAILURE",
        "exception_type": "RuntimeError",
        "exception_payload": result,
        "failure_capture_to_decision_ms":
            (DECIDED_NS_FROM_RETAINED_EXCEPTION - observation["capture_ns"]) / 1e6,
        "input_operations": 0,
        "model_calls": 0,
        "missing_cleanup_evidence": ["owner-events.json", "post_control_score", "wrapper process exit code"],
        "root_cause": "probe initialized both WAD glyph readers after the source capture; v34 initializes readers before launching the runtime",
        "transcription": "controller_decided_ns and exception type copied from the retained first-run stderr shown by the allocation launcher; the result is deterministically reconstructed here",
        "scope": plan["scope"],
    }
    checks = {
        "frozen_sources_match": all(sha(REPO / name) == digest
                                    for name, digest in plan["source_sha256"].items()),
        "only_clock_ready_observation": [row["event"] for row in events] ==
                                        ["clock_probe", "ready", "observation"],
        "no_command_or_input": not any(row.get("event") in
            ("command", "accepted", "input_admission", "keys_held") for row in events),
        "stale_before_input": result["status"] == "REJECTED_STALE" and
                              result["action_may_proceed_to_executor_admission"] is False,
        "age_exceeded_frozen_bound": failure["failure_capture_to_decision_ms"] >
                                     authored["max_current_age_ms"],
        "failure_artifacts_not_overclaimed": len(failure["missing_cleanup_evidence"]) == 3,
    }
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE / "runtime", TARGET / "runtime")
    shutil.copy2(PREREG, TARGET / "preregistration.json")
    (TARGET / "failure.json").write_text(
        json.dumps(failure, indent=2) + "\n", encoding="utf-8", newline="\n")
    audit = {"audit_passed": all(checks.values()), "allocation_passed": False,
             "decision": failure["disposition"], "checks": checks,
             "events": len(events), "observations": len(observations),
             "initial_image_sha256": sha(SOURCE / "runtime/001.png"),
             "initial_packet_sha256": sha(SOURCE / "runtime/001.ait"),
             "failure_capture_to_decision_ms": failure["failure_capture_to_decision_ms"],
             "limits": "pre-input retained failure; absence of a surviving process was inspected posthoc but is not durable cleanup proof"}
    (TARGET / "audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))
    return 0 if audit["audit_passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
