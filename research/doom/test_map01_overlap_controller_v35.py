import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "live_control"))
import map01_overlap_controller_v35 as controller
from persistent_planner_adapter_v2 import _validate_schema, PlannerProtocolError
from running_action_guard_v1 import RunningActionGuard
from running_action_guard_v2 import RunningActionGuardV2
from executor_v10 import program_sha256


BINDING = {"focus": 1, "surface": 1, "geometry": [0, 0, 640, 480]}


def signal(signal_id, value, sequence, capture_ns, status="observed"):
    return {"format": "observable-signal-v1", "status": status,
            "signal_id": signal_id, "value": value if status == "observed" else None,
            "sequence": sequence, "capture_ns": capture_ns, "binding": BINDING}


def action(command="retreat_fire", minimum_ammo=1):
    return {"assessment": "bounded action remains applicable under typed evidence",
            "state": "active",
            "commands": [{"action": command, "extent": "short"}],
            "contingencies": [],
            "next_cover": [{"action": "strafe_left", "extent": "short"}],
            "next_cover_validity": [{"signal_id": "health",
                                     "critical_health_minimum": 45,
                                     "maximum_health_loss": 8,
                                     "max_source_age_ms": 30000}],
            "action_validity": [{"critical_health_minimum": 45,
                                 "maximum_health_loss": 8,
                                 "minimum_ammo": minimum_ammo,
                                 "max_current_age_ms": 500}]}


def initial_receipt():
    result = SimpleNamespace(handle=SimpleNamespace(turn_id="turn-1"),
                             status="completed", answer_eligible=True)
    return controller.final_admission_from_planner_result(result, 10, None, 11)


class Map01OverlapControllerV35Tests(unittest.TestCase):
    def running_guard(self):
        candidate = action()
        ready = controller.prepare_action_admission(
            initial_receipt(), candidate, candidate["action_validity"][0],
            signal("health", 85, 1, 100), signal("ammo", 47, 1, 100),
            signal("health", 85, 2, 200), signal("ammo", 47, 2, 200), 201)
        return candidate, RunningActionGuard(
            candidate["commands"], ready["action_validity"]["contract"],
            ready["action_validity"])

    def test_schema_and_semantics_require_separate_action_validity(self):
        candidate = action()
        schema = json.loads((HERE / "map01_cover_policy_schema_v6.json").read_text())
        _validate_schema(candidate, schema)
        controller.validate_action(candidate)
        missing = copy.deepcopy(candidate); missing["action_validity"] = []
        with self.assertRaises(ValueError):
            controller.validate_action(missing)
        terminal = {"assessment": "dead", "state": "dead", "commands": [],
                    "contingencies": [], "next_cover": [],
                    "next_cover_validity": [], "action_validity": []}
        _validate_schema(terminal, schema)
        controller.validate_action(terminal)
        malformed = copy.deepcopy(candidate)
        malformed["action_validity"][0]["max_current_age_ms"] = 1001
        with self.assertRaises(PlannerProtocolError):
            _validate_schema(malformed, schema)

    def test_fire_reaches_executor_ready_only_after_current_health_and_ammo(self):
        candidate = action()
        ready = controller.prepare_action_admission(
            initial_receipt(), candidate, candidate["action_validity"][0],
            signal("health", 85, 1, 100), signal("ammo", 47, 1, 100),
            signal("health", 79, 2, 200), signal("ammo", 46, 2, 200), 201)
        self.assertEqual(ready["status"], "READY_FOR_FRESH_EXECUTOR_ADMISSION")
        self.assertEqual([row["signal_id"] for row in
                          ready["action_validity"]["checks"]],
                         ["health", "health", "ammo"])
        admitted = controller.bind_first_plan_acceptance(
            ready, {"id": "primary", "accepted_ns": 202})
        self.assertEqual(admitted["status"], "INPUT_ADMITTED")

    def test_zero_or_unknown_ammo_rejects_before_executor(self):
        candidate = action()
        for current in (signal("ammo", 0, 2, 200),
                        signal("ammo", 0, 2, 200, status="unknown")):
            rejected = controller.prepare_action_admission(
                initial_receipt(), candidate, candidate["action_validity"][0],
                signal("health", 85, 1, 100), signal("ammo", 47, 1, 100),
                signal("health", 79, 2, 200), current, 201)
            self.assertEqual(rejected["status"], "REJECTED_ACTION_NOT_CURRENT")
            self.assertIsNone(rejected["executor_admission"])

    def test_fire_cannot_omit_ammo_and_movement_cannot_add_it(self):
        with self.assertRaises(ValueError):
            candidate = action(minimum_ammo=0)
            controller.prepare_action_admission(
                initial_receipt(), candidate, candidate["action_validity"][0],
                signal("health", 85, 1, 100), signal("ammo", 47, 1, 100),
                signal("health", 79, 2, 200), signal("ammo", 46, 2, 200), 201)
        with self.assertRaises(ValueError):
            candidate = action(command="strafe_left", minimum_ammo=1)
            controller.prepare_action_admission(
                initial_receipt(), candidate, candidate["action_validity"][0],
                signal("health", 85, 1, 100), signal("ammo", 47, 1, 100),
                signal("health", 79, 2, 200), signal("ammo", 46, 2, 200), 201)

    def test_prompt_exposes_exact_source_epoch_health_and_ammo(self):
        class Planner:
            def begin_turn(self, prompt, **params):
                self.prompt, self.params = prompt, params
                return "handle"
        planner = Planner()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); image = root / "sheet.png"; image.write_bytes(b"x")
            with patch.object(controller, "win", return_value=r"C:\sheet.png"):
                controller.begin_model_turn(
                    planner, root, image, [], 85, 47, None, {"type": "object"})
        self.assertIn("Current locally verified health: 85", planner.prompt)
        self.assertIn("Current locally verified ammo: 47", planner.prompt)

    def test_running_monitor_uses_same_observation_for_health_and_ammo(self):
        class Reader:
            def __init__(self, name): self.name = name
            def read(self, row):
                return signal(self.name, row[self.name], row["sequence"], row["capture_ns"])
        _, guard = self.running_guard()
        guard.admit_program({"event": "accepted", "id": "p1", "accepted_ns": 202})
        monitor = controller.DoomRunningActionMonitor(
            guard, Reader("health"), Reader("ammo"))
        current = {"sequence": 3, "capture_ns": 300,
                   "pointer_binding": BINDING, "health": 84, "ammo": 46}
        self.assertIsNone(monitor.observe(current, 301))
        current.update({"sequence": 4, "capture_ns": 400, "health": 76})
        invalidation = monitor.observe(current, 401)
        self.assertEqual(invalidation["event"], "running_action_invalidation")
        self.assertEqual(invalidation["running_action_guard"]["state"], "CANCEL_REQUIRED")
        self.assertEqual(invalidation["running_action_guard"]["invalidation"]["result"]["reason"],
                         "health_max_decrease_from_source_failed")

    def test_cancel_helper_requires_matched_cancel_and_empty_release(self):
        class Stream:
            def __init__(self): self.writes = []
            def write(self, value): self.writes.append(value)
            def flush(self): pass
        class Process:
            def __init__(self): self.stdin = Stream()
        _, guard = self.running_guard()
        guard.admit_program({"event": "accepted", "id": "p1", "accepted_ns": 202})
        invalid = {"format": "action-admission-snapshot-v1", "sequence": 3,
                   "capture_ns": 300, "binding": BINDING,
                   "signals": {"health": {"status": "observed", "value": 70},
                               "ammo": {"status": "observed", "value": 46}}}
        guard.check_current(invalid, 301)
        rows = iter([
            {"event": "cancel_requested", "id": "p1", "matched": True,
             "requested_ns": 302, "emit_ns": 303},
            {"event": "terminal", "id": "p1", "status": "cancelled",
             "terminal_ns": 305, "release": {"verified": True,
             "keys_down": [], "buttons_down": [], "verified_ns": 304}}])
        def wait(predicate):
            row = next(rows); self.assertTrue(predicate(row)); return row
        process = Process()
        _, terminal, receipt = controller.cancel_invalidated_action(
            process, wait, "p1", guard)
        self.assertEqual(json.loads(process.stdin.writes[0]), {"op": "cancel", "id": "p1"})
        self.assertEqual(terminal["status"], "cancelled")
        self.assertEqual(receipt["state"], "REVOKED_ACTION_NOT_CURRENT")
        self.assertTrue(receipt["physical_release_verified"])

    def test_v2_monitor_exposes_one_root_authority_and_exact_compiler(self):
        class Reader:
            def __init__(self, name): self.name = name
            def read(self, row):
                return signal(self.name, row[self.name], row["sequence"], row["capture_ns"])
        candidate = action()
        ready = controller.prepare_action_admission(
            initial_receipt(), candidate, candidate["action_validity"][0],
            signal("health", 85, 1, 100), signal("ammo", 47, 1, 100),
            signal("health", 85, 2, 200), signal("ammo", 47, 2, 200), 201)
        guard = RunningActionGuardV2(
            candidate, ready, controller.compile_commands,
            "map01_overlap_controller_v35.compile_commands")
        steps = controller.compile_commands(candidate["commands"])
        command = {"op": "submit", "id": "p1", "expected_sequence": 2,
                   "valid_until_ns": 1000, "steps": steps}
        receipt = guard.admit_program(
            {"role": "primary", "semantic_commands": candidate["commands"],
             "command_indices": [0], "contingency_after": None,
             "compiled_steps": steps},
            {"command": command, "sent_ns": 202},
            {"event": "accepted", "id": "p1", "steps": 1,
             "program_sha256": program_sha256(steps),
             "accepted_ns": 203})
        self.assertTrue(receipt["current_input_authority"])
        self.assertEqual(receipt["historical_first_admission"]["id"], "p1")
        monitor = controller.DoomRunningActionMonitor(
            guard, Reader("health"), Reader("ammo"))
        current = {"sequence": 3, "capture_ns": 300,
                   "pointer_binding": BINDING, "health": 84, "ammo": 46}
        self.assertIsNone(monitor.observe(current, 301))
        self.assertTrue(monitor.last_receipt["current_input_authority"])
        self.assertEqual(monitor.last_receipt["compiler_identity"],
                         "map01_overlap_controller_v35.compile_commands")


if __name__ == "__main__":
    unittest.main()
