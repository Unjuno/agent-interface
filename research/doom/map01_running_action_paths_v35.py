"""Deterministic program-binding/current-authority composition paths for v35."""
import argparse
import json
from pathlib import Path
import sys
from types import SimpleNamespace


HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "live_control")]
import map01_overlap_controller_v35 as controller
from running_action_guard_v2 import RunningActionGuardV2
from executor_v10 import program_sha256


BINDING = {"focus": 7, "surface": 8, "geometry": [0, 0, 640, 480]}
COMMANDS = [{"action": "forward", "extent": "short"},
            {"action": "fire", "extent": "pulse"}]
FALLBACK = [{"action": "retreat_fire", "extent": "short"}]


def signal(signal_id, value, sequence, capture_ns):
    return {"format": "observable-signal-v1", "status": "observed",
            "signal_id": signal_id, "value": value, "sequence": sequence,
            "capture_ns": capture_ns, "binding": BINDING}


def snapshot(sequence, capture_ns, health=90, ammo=12):
    return {"format": "action-admission-snapshot-v1", "sequence": sequence,
            "capture_ns": capture_ns, "binding": BINDING,
            "signals": {"health": {"status": "observed", "value": health},
                        "ammo": {"status": "observed", "value": ammo}}}


def action():
    return {"assessment": "deterministic v35 composition", "state": "active",
            "commands": list(COMMANDS),
            "contingencies": [{"after_command": 0,
                "condition": "no_visible_effect", "commands": list(FALLBACK)}],
            "next_cover": [],
            "next_cover_validity": [{"signal_id": "health",
                "critical_health_minimum": 40, "maximum_health_loss": 10,
                "max_source_age_ms": 30000}],
            "action_validity": [{"critical_health_minimum": 40,
                "maximum_health_loss": 10, "minimum_ammo": 1,
                "max_current_age_ms": 500}]}


def ready(candidate):
    planner = SimpleNamespace(handle=SimpleNamespace(turn_id="turn-v35"),
                              status="completed", answer_eligible=True)
    receipt = controller.final_admission_from_planner_result(planner, 10, None, 11)
    return controller.prepare_action_admission(
        receipt, candidate, candidate["action_validity"][0],
        signal("health", 90, 1, 100), signal("ammo", 12, 1, 100),
        signal("health", 90, 2, 200), signal("ammo", 12, 2, 200), 201)


def program(role, commands, indices, after=None):
    return {"role": role, "semantic_commands": commands,
            "command_indices": indices, "contingency_after": after,
            "compiled_steps": controller.compile_commands(commands)}


def admit(guard, identifier, value, sent, accepted, branch=None):
    command = {"op": "submit", "id": identifier, "expected_sequence": 2,
               "valid_until_ns": accepted + 1000,
               "steps": value["compiled_steps"]}
    return guard.admit_program(
        value, {"command": command, "sent_ns": sent},
        {"event": "accepted", "id": identifier,
         "steps": len(value["compiled_steps"]),
         "program_sha256": program_sha256(value["compiled_steps"]),
         "accepted_ns": accepted},
        branch_evidence=branch)


def terminal(identifier, status, at):
    return {"event": "terminal", "id": identifier, "status": status,
            "terminal_ns": at, "release": {"verified": True,
            "keys_down": [], "buttons_down": [], "verified_ns": at - 1}}


def new_guard():
    candidate = action()
    return candidate, RunningActionGuardV2(
        candidate, ready(candidate), controller.compile_commands,
        "map01_overlap_controller_v35.compile_commands")


def run():
    rows = []

    candidate, guard = new_guard()
    whole = program("primary", candidate["commands"], [0, 1])
    admit(guard, "whole", whole, 202, 203)
    guard.check_current(snapshot(3, 300), 301)
    rows.append(("one_primary_bundle",
        guard.record_completed_terminal(terminal("whole", "completed", 310), final=True), 1))

    candidate, guard = new_guard()
    first = program("primary", candidate["commands"][:1], [0])
    admit(guard, "segment-0", first, 202, 203)
    guard.check_current(snapshot(3, 300), 301)
    guard.record_completed_terminal(terminal("segment-0", "completed", 310))
    guard.check_current(snapshot(4, 320), 321)
    second = program("primary", candidate["commands"][1:], [1])
    admit(guard, "segment-1", second, 322, 323)
    guard.check_current(snapshot(5, 400), 401)
    rows.append(("two_primary_segments",
        guard.record_completed_terminal(terminal("segment-1", "completed", 410), final=True), 2))

    candidate, guard = new_guard()
    first = program("primary", candidate["commands"][:1], [0])
    admit(guard, "branch-primary", first, 202, 203)
    guard.check_current(snapshot(3, 300), 301)
    guard.record_completed_terminal(terminal("branch-primary", "completed", 310))
    guard.check_current(snapshot(4, 320), 321)
    fallback = program("fallback", candidate["contingencies"][0]["commands"], [0], 0)
    branch = {"after_command": 0, "condition": "no_visible_effect",
              "primary_program_id": "branch-primary", "command_index": 0,
              "semantic_command": candidate["commands"][0],
              "effect_receipt": {"action": "forward", "extent": "short",
                  "result": "no_visible_effect", "effect_observed_ns": 309}}
    admit(guard, "branch-fallback", fallback, 322, 323, branch)
    guard.check_current(snapshot(5, 400), 401)
    rows.append(("fallback_branch",
        guard.record_completed_terminal(terminal("branch-fallback", "completed", 410), final=True), 2))

    candidate, guard = new_guard()
    first = program("primary", candidate["commands"][:1], [0])
    admit(guard, "active-invalid", first, 202, 203)
    guard.check_current(snapshot(3, 300, health=70), 301)
    guard.record_cancel_requested({"event": "cancel_requested", "id": "active-invalid",
                                   "matched": True, "requested_ns": 302})
    rows.append(("active_invalidation",
        guard.record_cancelled_terminal(terminal("active-invalid", "cancelled", 305)), 1))

    candidate, guard = new_guard()
    first = program("primary", candidate["commands"][:1], [0])
    admit(guard, "between-invalid", first, 202, 203)
    guard.check_current(snapshot(3, 300), 301)
    guard.record_completed_terminal(terminal("between-invalid", "completed", 310))
    rows.append(("intersegment_invalidation",
                 guard.check_current(snapshot(4, 320, health=70), 321), 1))

    cases = []
    for name, receipt, expected_programs in rows:
        assert len(receipt["program_bindings"]) == expected_programs
        assert receipt["current_input_authority"] is False
        assert receipt["physical_release_verified"] is True
        assert receipt["historical_first_admission"] is not None
        for binding in receipt["program_bindings"]:
            assert (
                binding["submit"]["command"]["steps"]
                == binding["program"]["compiled_steps"]
            )
            assert (
                binding["accepted"]["program_sha256"]
                == program_sha256(binding["program"]["compiled_steps"])
            )
        cases.append({"case": name, "state": receipt["state"],
                      "program_bindings": expected_programs,
                      "current_input_authority": False,
                      "physical_release_verified": True,
                      "receipt": receipt})
    return {"schema": "map01-running-action-paths-v35", "passed": True,
            "cases": cases, "case_count": len(cases),
            "program_bindings": sum(row["program_bindings"] for row in cases),
            "executor_attestations": sum(row["program_bindings"] for row in cases),
            "current_authority_true_at_terminal": 0,
            "model_calls": 0, "input_operations": 0,
            "limits": "deterministic composition only; no endpoint, game, planner authorship, timing or task claim"}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(); result = run(); args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "audit.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"passed": result["passed"], "case_count": result["case_count"],
                      "program_bindings": result["program_bindings"],
                      "executor_attestations": result["executor_attestations"]},
                     separators=(",", ":")))


if __name__ == "__main__": main()
