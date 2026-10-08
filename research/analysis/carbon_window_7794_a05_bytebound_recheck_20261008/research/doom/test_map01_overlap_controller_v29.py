import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULT = HERE / "results/map01-fixed-threat-v28-live-01"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "live_control"))
import map01_overlap_controller_v29 as controller
from doom_hud_signal_v1 import DoomStatusNumberReader
from persistent_planner_adapter_v2 import _validate_schema
from persistent_planner_adapter_v2 import PlannerProtocolError


class FakePlanner:
    def __init__(self):
        self.calls = []

    def begin_turn(self, prompt, **params):
        self.calls.append((prompt, params))
        return "handle"

    def interrupt(self, handle):
        self.calls.append(("interrupt", handle))
        return {"outcome": "requested"}


class FakeInput:
    def __init__(self):
        self.writes = []
        self.flushes = 0

    def write(self, value):
        self.writes.append(value)

    def flush(self):
        self.flushes += 1


class FakeProcess:
    def __init__(self):
        self.stdin = FakeInput()


class Map01TypedCoverValidityV29Tests(unittest.TestCase):
    def observations(self):
        return {row["sequence"]: row for row in (
            json.loads(line) for line in
            (RESULT / "runtime/events.jsonl").read_text().splitlines())
            if row.get("event") == "observation"}

    def reader(self):
        return DoomStatusNumberReader(
            controller.WAD,
            image_resolver=lambda value: RESULT / "runtime" / Path(value).name)

    def active_action(self):
        return {
            "assessment": "visible threat; strafe remains valid above critical health",
            "state": "active",
            "commands": [{"action": "fire", "extent": "pulse"}],
            "contingencies": [],
            "next_cover": [{"action": "strafe_left", "extent": "short"}],
            "next_cover_validity": [{"signal_id": "health", "hard_minimum": 80,
                                     "max_source_age_ms": 30000}],
        }

    def test_schema_and_semantic_contract_require_typed_validity(self):
        action = self.active_action()
        schema = json.loads((HERE / "map01_cover_policy_schema_v4.json").read_text())
        _validate_schema(action, schema)
        controller.validate_action(action)
        missing = copy.deepcopy(action)
        missing["next_cover_validity"] = []
        with self.assertRaises(ValueError):
            controller.validate_action(missing)
        too_wide = copy.deepcopy(action)
        too_wide["next_cover_validity"][0]["hard_minimum"] = 0
        with self.assertRaises(PlannerProtocolError):
            _validate_schema(too_wide, schema)
        terminal = {"assessment": "dead", "state": "dead", "commands": [],
                    "contingencies": [], "next_cover": [], "next_cover_validity": []}
        _validate_schema(terminal, schema)
        controller.validate_action(terminal)

    def test_reusable_cover_keeps_authored_envelope(self):
        action = self.active_action()
        cover, validity, iteration = controller.reusable_cover([
            {"iteration": 4, "action": action, "model_action_discarded": False}])
        self.assertEqual(cover, action["next_cover"])
        self.assertEqual(validity, action["next_cover_validity"][0])
        self.assertEqual(iteration, 4)
        self.assertEqual(controller.reusable_cover([]), ([], None, None))

    def test_retained_trace_soft_preserves_then_hard_invalidates(self):
        observations = self.observations()
        monitor, admission = controller.build_cover_monitor(
            self.reader(), observations[37],
            {"signal_id": "health", "hard_minimum": 80,
             "max_source_age_ms": 30000}, 2)
        self.assertEqual(admission["status"], "admitted")
        self.assertFalse(admission["grants_input_authority"])
        self.assertIsNone(monitor.observe(observations[51]))
        self.assertIsNone(monitor.observe(observations[60]))
        event = monitor.observe(observations[68])
        self.assertEqual(monitor.soft_event_count, 2)
        self.assertEqual(event["outcome"]["status"], "HARD_INVALIDATED")
        self.assertFalse(event["outcome"]["keep_existing_policy"])

    def test_breached_authored_floor_rejects_cover_and_uses_strict_source(self):
        observations = self.observations()
        monitor, admission = controller.build_cover_monitor(
            self.reader(), observations[68],
            {"signal_id": "health", "hard_minimum": 80,
             "max_source_age_ms": 30000}, 3)
        self.assertEqual(admission["status"], "rejected_source_below_hard_minimum")
        self.assertEqual(admission["source_signal"]["value"], 79)
        self.assertEqual(admission["effective"]["hard_minimum"], 79)
        event = monitor.observe(observations[70])
        self.assertEqual(event["outcome"]["status"], "HARD_INVALIDATED")

    def test_overwide_authored_loss_envelope_rejects_cover(self):
        observations = self.observations()
        _, admission = controller.build_cover_monitor(
            self.reader(), observations[37],
            {"signal_id": "health", "hard_minimum": 1,
             "max_source_age_ms": 30000}, 3)
        self.assertEqual(admission["status"], "rejected_health_loss_envelope_too_wide")
        self.assertEqual(admission["effective"]["hard_minimum"], 93)
        commands = [{"action": "strafe_left", "extent": "short"}]
        self.assertEqual(controller.admitted_cover_commands(commands, admission), [])
        admitted = copy.deepcopy(admission)
        admitted["status"] = "admitted"
        self.assertEqual(controller.admitted_cover_commands(commands, admitted), commands)

    def test_hard_event_interrupts_cancels_and_requires_verified_empty_release(self):
        planner = FakePlanner()
        process = FakeProcess()
        terminal = {"event": "terminal", "id": "cover-2", "status": "cancelled",
                    "release": {"verified": True, "buttons_down": [], "keys_down": []}}
        seen = []

        def wait(predicate):
            seen.append(predicate)
            self.assertTrue(predicate(terminal))
            return terminal

        interrupt, observed_terminal = controller.cancel_invalidated_cover(
            planner, "turn-2", process, wait, "cover-2")
        self.assertEqual(interrupt["outcome"], "requested")
        self.assertEqual(observed_terminal, terminal)
        self.assertEqual(planner.calls, [("interrupt", "turn-2")])
        self.assertEqual(process.stdin.writes,
                         [json.dumps({"op": "cancel", "id": "cover-2"}) + "\n"])
        self.assertEqual(process.stdin.flushes, 1)

        bad = copy.deepcopy(terminal)
        bad["release"]["keys_down"] = ["a"]
        with self.assertRaises(RuntimeError):
            controller.cancel_invalidated_cover(
                FakePlanner(), "turn-3", FakeProcess(), lambda predicate: bad, "cover-3")

    def test_prompt_exposes_checked_health_without_image_retranscription(self):
        planner = FakePlanner()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "sheet.png"
            image.write_bytes(b"fixture")
            with patch.object(controller, "win", return_value=r"C:\sheet.png"):
                controller.begin_model_turn(
                    planner, root, image, ["forward"], 93, {"type": "object"})
        prompt, _ = planner.calls[0]
        self.assertIn("Current locally verified health: 93", prompt)


if __name__ == "__main__":
    unittest.main()
