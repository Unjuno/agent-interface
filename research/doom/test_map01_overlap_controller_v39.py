"""Regression for the v38 rejected-action -> unauthored coast interrupt loop."""
import ast
import json
import sys
import unittest
from argparse import Namespace
from pathlib import Path
import types


HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "live_control")]
import map01_overlap_controller_v39 as controller


class Map01V39CoastTests(unittest.TestCase):
    def test_invalidated_rejected_renewal_interrupts_without_cancelling_unadmitted_id(self):
        class Stdin:
            def __init__(self): self.writes = []
            def write(self, value): self.writes.append(value)
            def flush(self): pass
        class Process:
            def __init__(self): self.stdin = Stdin()
        class Planner:
            def __init__(self): self.interrupted = []
            def interrupt(self, handle):
                self.interrupted.append(handle)
                return {"status": "interrupted"}

        previous_terminal = {"event": "terminal", "id": "cover-0",
                             "status": "completed",
                             "release": {"verified": True,
                                          "keys_down": [], "buttons_down": []}}
        rejected = {"event": "rejected", "reason": "stale_sequence"}
        planner, process, handle = Planner(), Process(), object()
        cover_ids = ["cover-0"]
        wait_calls = []

        def wait(predicate):
            wait_calls.append(predicate)
            self.assertTrue(predicate(rejected))
            return rejected

        interruption, terminal, admitted = controller.resolve_invalidated_cover_renewal(
            planner, handle, process, wait, "cover-0-renew-1", cover_ids,
            previous_terminal)

        self.assertEqual(interruption, {"status": "interrupted"})
        self.assertIs(terminal, previous_terminal)
        self.assertFalse(admitted)
        self.assertEqual(planner.interrupted, [handle])
        self.assertEqual(process.stdin.writes, [])
        self.assertEqual(len(wait_calls), 1)
        self.assertEqual(cover_ids, ["cover-0"])

    def test_invalidated_accepted_renewal_is_cancelled_and_release_verified(self):
        class Stdin:
            def __init__(self): self.writes = []
            def write(self, value): self.writes.append(value)
            def flush(self): pass
        class Process:
            def __init__(self): self.stdin = Stdin()
        class Planner:
            def __init__(self): self.interrupted = []
            def interrupt(self, handle):
                self.interrupted.append(handle)
                return {"status": "interrupted"}

        cover_id = "cover-0-renew-1"
        response = {"event": "accepted", "id": cover_id}
        terminal = {"event": "terminal", "id": cover_id, "status": "cancelled",
                    "release": {"verified": True,
                                "keys_down": [], "buttons_down": []}}
        planner, process, handle = Planner(), Process(), object()
        cover_ids = ["cover-0"]
        events = iter((response, terminal))

        def wait(predicate):
            row = next(events)
            self.assertTrue(predicate(row))
            return row

        interruption, actual_terminal, admitted = controller.resolve_invalidated_cover_renewal(
            planner, handle, process, wait, cover_id, cover_ids,
            {"event": "terminal", "id": "cover-0", "status": "completed",
             "release": {"verified": True, "keys_down": [], "buttons_down": []}})

        self.assertEqual(interruption, {"status": "interrupted"})
        self.assertIs(actual_terminal, terminal)
        self.assertTrue(admitted)
        self.assertEqual(planner.interrupted, [handle])
        self.assertEqual(cover_ids, ["cover-0", cover_id])
        self.assertEqual(len(process.stdin.writes), 1)
        self.assertIn('"id": "cover-0-renew-1"', process.stdin.writes[0])


    def test_session_command_keeps_v12_default_and_selects_v15_only_when_opted_in(self):
        args = Namespace(seed=990605, load_fixture_manifest=Path("fixture.json"))
        default = controller.session_command(args, Path("runtime"))
        self.assertEqual(Path(default[1]).name, "session_map01_v12.py")
        self.assertIn("--out", default)
        self.assertIn("--load-fixture-manifest", default)

        args.measurement_session = True
        measured = controller.session_command(args, Path("runtime"))
        self.assertEqual(Path(measured[1]).name, "session_map01_v15.py")
        self.assertEqual(measured[2:], default[2:])

    def test_rejected_action_followup_keeps_model_turn_alive_on_damage(self):
        previous = {"iteration": 1, "model_action_discarded": True,
                    "action": {"state": "active", "next_cover": [
                        {"action": "strafe_left", "extent": "short"}],
                        "next_cover_validity": [{"signal_id": "health",
                            "critical_health_minimum": 35,
                            "maximum_health_loss": 12,
                            "max_source_age_ms": 30000}]}}
        commands, validity, source = controller.reusable_cover([previous])
        self.assertEqual((commands, validity, source), ([], None, None))
        default_receipt = {"authored": None, "effective": {
            "hard_minimum": 85, "maximum_health_loss": 0}}
        selected, receipt = controller.select_cover_monitor(
            object(), default_receipt, commands, source)
        self.assertIsInstance(selected, controller.UnauthoredCoastMonitor)
        self.assertEqual(receipt["monitor_mode"], "unauthored_coast_no_policy")
        self.assertEqual(selected.event_types, frozenset())
        self.assertEqual(selected.soft_event_count, 0)
        self.assertIsNone(selected.latest_soft_event)
        # The exact frame still updates latest in the caller, while the
        # unauthored coast publishes no policy event that can interrupt.
        self.assertEqual(default_receipt["effective"]["hard_minimum"], 85)

    def test_authored_cover_still_uses_original_guard(self):
        guard = object()
        authored = {"signal_id": "health", "critical_health_minimum": 35,
                    "maximum_health_loss": 12, "max_source_age_ms": 30000}
        selected, receipt = controller.select_cover_monitor(
            guard, {"authored": authored},
            [{"action": "strafe_left", "extent": "short"}], 0)
        self.assertIs(selected, guard)
        self.assertEqual(receipt["monitor_mode"], "authored_policy_guard")
        self.assertEqual(receipt["authored"], authored)

    def test_running_invalidation_interrupts_planner_and_requires_verified_empty_release(self):
        class Stdin:
            def __init__(self): self.writes = []
            def write(self, value): self.writes.append(value)
            def flush(self): pass
        class Process:
            def __init__(self): self.stdin = Stdin()
        class Planner:
            def __init__(self): self.interrupted = []
            def interrupt(self, handle):
                self.interrupted.append(handle)
                return {"status": "interrupted"}
        terminal = {"event": "terminal", "id": "cover-0", "status": "cancelled",
                    "release": {"verified": True, "keys_down": [], "buttons_down": []}}
        process, planner, handle = Process(), Planner(), object()

        interruption, result = controller.cancel_invalidated_cover(
            planner, handle, process, lambda predicate: terminal, "cover-0")

        self.assertIs(result, terminal)
        self.assertEqual(planner.interrupted, [handle])
        self.assertEqual(interruption, {"status": "interrupted"})
        self.assertIn('"op": "cancel"', process.stdin.writes[0])

    def test_running_invalidation_rejects_nonempty_or_unverified_release(self):
        class Stdin:
            def write(self, value): pass
            def flush(self): pass
        class Process:
            stdin = Stdin()
        class Planner:
            def interrupt(self, handle): return {"status": "interrupted"}
        for release in (
            {"verified": False, "keys_down": [], "buttons_down": []},
            {"verified": True, "keys_down": ["W"], "buttons_down": []},
            {"verified": True, "keys_down": [], "buttons_down": ["fire"]},
        ):
            terminal = {"event": "terminal", "id": "cover-0", "status": "cancelled",
                        "release": release}
            with self.subTest(release=release):
                with self.assertRaisesRegex(RuntimeError, "verify empty release"):
                    controller.cancel_invalidated_cover(
                        Planner(), object(), Process(), lambda predicate: terminal, "cover-0")

    def test_main_resolves_renewal_admission_before_cancellation(self):
        tree = ast.parse(Path(controller.__file__).read_bytes())
        main = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == "main")
        branch = next(node for node in ast.walk(main)
                      if isinstance(node, ast.If) and
                      "next_accepted" in ast.dump(node.test) and
                      "policy_invalidation" in ast.dump(node.test))
        branch_source = ast.unparse(branch)
        self.assertIn("resolve_invalidated_cover_renewal", branch_source)
        self.assertIn("if renewal_admitted", branch_source)
        self.assertIn("cover_terminals.append(current_terminal)", branch_source)
        self.assertNotIn("current_cover = next_cover", branch_source)

if __name__ == "__main__":
    unittest.main()
