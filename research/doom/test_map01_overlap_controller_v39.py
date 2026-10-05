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


def extract_renewal_invalidation_branch():
    tree = ast.parse(Path(controller.__file__).read_bytes())
    main = next(node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "main")
    branch = next(node for node in ast.walk(main)
                  if isinstance(node, ast.If) and
                  any(isinstance(child, ast.Name) and child.id == "next_accepted"
                      for child in ast.walk(node.test)) and
                  "policy_invalidation" in ast.dump(node.test))
    factory = ast.parse(
        "def factory(next_accepted, next_cover, planner, planner_handle, "
        "process, wait, cover_terminals):\n"
        "    invalidation = None\n"
        "    current_cover = 'cover-0'\n"
        "    current_terminal = None\n"
        "    planner_interrupt = None\n").body[0]
    factory.body.extend([branch, ast.parse("break").body[0]])
    factory.body = [ast.While(test=ast.Constant(value=True),
                              body=factory.body, orelse=[])]
    factory.body += ast.parse(
        "return invalidation, current_cover, planner_interrupt, "
        "current_terminal, cover_terminals\n").body
    module = ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[]))
    scope = {"cancel_invalidated_cover": controller.cancel_invalidated_cover}
    exec(compile(module, str(controller.__file__), "exec"), scope)
    return scope["factory"]


class Map01V39CoastTests(unittest.TestCase):
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

    def test_renewal_invalidation_interrupts_planner_and_cancels_current_cover(self):
        invalidation = {"reason": "health_below_floor", "sequence": 18}
        terminal = {"event": "terminal", "id": "cover-renew-1",
                    "status": "cancelled", "release": {
                        "verified": True, "keys_down": [], "buttons_down": []}}

        class Stdin:
            def __init__(self): self.writes = []
            def write(self, value): self.writes.append(value)
            def flush(self): pass

        class Planner:
            def __init__(self): self.interrupted = []
            def interrupt(self, handle):
                self.interrupted.append(handle)
                return {"status": "interrupted"}

        process = types.SimpleNamespace(stdin=Stdin())
        planner = Planner()
        handle = object()

        def wait(predicate):
            self.assertTrue(predicate(terminal))
            return terminal

        cover_terminals = []
        result = extract_renewal_invalidation_branch()(
            {"event": "policy_invalidation", "invalidation": invalidation},
            "cover-renew-1", planner, handle, process, wait, cover_terminals)

        self.assertEqual(result[:2], (invalidation, "cover-renew-1"))
        self.assertEqual(result[2], {"status": "interrupted"})
        self.assertIs(result[3], terminal)
        self.assertEqual(result[4], [terminal])
        self.assertEqual(planner.interrupted, [handle])
        self.assertEqual(json.loads(process.stdin.writes[0]),
                         {"op": "cancel", "id": "cover-renew-1"})


if __name__ == "__main__":
    unittest.main()
