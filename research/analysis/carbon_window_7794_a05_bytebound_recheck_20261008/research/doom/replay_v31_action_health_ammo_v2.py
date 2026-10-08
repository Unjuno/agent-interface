"""Exact-frame action-specific health/ammo validity replay over retained v31."""
import argparse
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/map01-soft-context-v31-live-01"
WAD = REPO / "_vizdoom/vizdoom/freedoom2.wad"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "live_control"))
from doom_action_validity_contract_v1 import FIRE_ACTIONS, build_contract
from doom_hud_signal_v2 import DoomStatusNumberReader
from research.live_control.action_validity_admission_v1 import (
    SNAPSHOT_FORMAT, evaluate_action_validity)


def run():
    report = json.loads((ROOT / "report.json").read_text())
    events = [json.loads(line) for line in
              (ROOT / "runtime/events.jsonl").read_text().splitlines()]
    observations = {row["sequence"]: row for row in events
                    if row.get("event") == "observation"}
    reader = lambda signal_id: DoomStatusNumberReader(
        WAD, signal_id=signal_id,
        image_resolver=lambda value: ROOT / "runtime" / Path(value).name)
    health_reader, ammo_reader = reader("health"), reader("ammo")
    rows = []
    for decision in report["decisions"]:
        if decision.get("plan_terminal") != "completed":
            continue
        source_sequence = decision["cover_validity_admission"]["source_signal"]["sequence"]
        current_sequence = decision["fresh_sequence_at_plan"]
        source_observation = observations[source_sequence]
        current_observation = observations[current_sequence]
        source_health = health_reader.read(source_observation)
        source_ammo = ammo_reader.read(source_observation)
        current_health = health_reader.read(current_observation)
        current_ammo = ammo_reader.read(current_observation)
        assert all(signal["status"] == "observed" for signal in
                   (source_health, source_ammo, current_health, current_ammo))
        commands = decision["action"]["commands"]
        uses_fire = any(command["action"] in FIRE_ACTIONS for command in commands)
        authored = {"critical_health_minimum": 45, "maximum_health_loss": 8,
                    "minimum_ammo": 1 if uses_fire else 0,
                    "max_current_age_ms": 500}
        contract = build_contract(
            commands, authored, source_health, source_ammo if uses_fire else None)
        current_signals = {
            "health": {"status": "observed", "value": current_health["value"]}}
        if uses_fire:
            current_signals["ammo"] = {
                "status": "observed", "value": current_ammo["value"]}
        snapshot = {"format": SNAPSHOT_FORMAT,
                    "sequence": current_sequence,
                    "capture_ns": current_health["capture_ns"],
                    "binding": current_health["binding"],
                    "signals": current_signals}
        accepted_ns = decision["execution_trace"][0]["accepted_ns"]
        result = evaluate_action_validity(commands, contract, snapshot, accepted_ns)
        rows.append({"iteration": decision["iteration"], "commands": commands,
                     "uses_fire": uses_fire,
                     "source": {"health": source_health["value"],
                                "ammo": source_ammo["value"]},
                     "current": {"health": current_health["value"],
                                 "ammo": current_ammo["value"]},
                     "status": result["status"], "result": result})
    assert len(rows) == 5 and sum(row["uses_fire"] for row in rows) == 3
    assert all(row["status"] == "VALID_CURRENT" for row in rows)
    fire = next(row for row in rows if row["uses_fire"])
    zero = json.loads(json.dumps(fire["result"]["snapshot"]))
    zero["signals"]["ammo"]["value"] = 0
    zero_result = evaluate_action_validity(
        fire["commands"], fire["result"]["contract"], zero,
        fire["result"]["controller_decided_ns"])
    assert zero_result["status"] == "REJECTED_PREDICATE"
    assert zero_result["reason"] == "ammo_minimum_failed"
    return {"schema": "retained-v31-action-health-ammo-replay-v2",
            "passed": True, "historical_rows": rows,
            "historical_candidate_passes": 5,
            "fire_action_contracts": 3, "nonfire_action_contracts": 2,
            "zero_ammo_control": zero_result,
            "model_calls": 0, "input_operations": 0,
            "finding": "exact current health plus action-specific ammunition predicates preserve five historical eligibility paths and reject a zero-ammo fire control",
            "limits": "synthetic authored specifications over retained frames; this does not establish planner authorship, target presence, aim, usefulness, latency improvement, gameplay gain, or generality"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "audit.json").write_bytes(
        (json.dumps(result, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"passed": result["passed"],
                      "historical_candidate_passes": result["historical_candidate_passes"],
                      "fire_action_contracts": result["fire_action_contracts"],
                      "zero_ammo_status": result["zero_ammo_control"]["status"]},
                     separators=(",", ":")))


if __name__ == "__main__":
    main()
