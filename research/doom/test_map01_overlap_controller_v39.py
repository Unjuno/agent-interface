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
    resolver = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "resolve_invalidated_cover_submission")
    factory = ast.parse(
        "def factory(next_accepted, next_cover, planner, planner_handle, "
        "process, wait, cover_terminals, cover_ids, current_cover, current_terminal):\n"
        "    invalidation = None\n"
        "    planner_interrupt = None\n"
        "    renewal_admission_resolution = None\n").body[0]
    factory.body = [ast.While(test=ast.Constant(value=True),
                              body=[branch, ast.parse("break").body[0]], orelse=[])]
    factory.body += ast.parse(
        "return (invalidation, current_cover, planner_interrupt, current_terminal, "
        "cover_terminals, cover_ids, renewal_admission_resolution)\n").body
    module = ast.fix_missing_locations(ast.Module(body=[resolver, factory], type_ignores=[]))
    scope = {"cancel_invalidated_cover": controller.cancel_invalidated_cover}
    exec(compile(module, str(controller.__file__), "exec"), scope)
    return scope["factory"]


class Map01V39CoastTests(unittest.TestCase):
    def test_accepted_first_renewal_keeps_monitor_until_final_plan_admission(self):
        source = Path(controller.__file__).read_text(encoding="utf-8")
        self.assertIn(
            "observation_monitor=invalidation_monitor)",
            source[source.index("while not future.done():"):source.index("planner_result=future.result()")],
        )
        invalidation_path = source[
            source.index("final_action_admission=final_admission_from_planner_result("):
            source.index('"terminal_candidate":True')
        ]
        self.assertIn("if invalidation is not None:", invalidation_path)
        self.assertIn('"model_action_discarded":True', invalidation_path)
        self.assertIn('"plan_terminal":"not_admitted"', invalidation_path)
        self.assertLess(
            source.index('"plan_terminal":"not_admitted"'),
            source.index("failure_cleanup.set_stage(\"action_admission\")"),
        )

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
        accepted = {"event": "accepted", "id": "cover-renew-1"}
        responses = [accepted, terminal]

        def wait(predicate):
            row = responses.pop(0)
            self.assertTrue(predicate(row))
            return row

        prior_terminal = {"event": "terminal", "id": "cover-0", "status": "expired",
                          "release": {"verified": True, "keys_down": [],
                                      "buttons_down": []}}
        cover_terminals = [prior_terminal]
        cover_ids = ["cover-0"]
        result = extract_renewal_invalidation_branch()(
            {"event": "policy_invalidation", "invalidation": invalidation},
            "cover-renew-1", planner, handle, process, wait, cover_terminals,
            cover_ids, "cover-0", prior_terminal)

        self.assertEqual(result[:2], (invalidation, "cover-renew-1"))
        self.assertEqual(result[2], {"status": "interrupted"})
        self.assertIs(result[3], terminal)
        self.assertEqual(result[4], [prior_terminal, terminal])
        self.assertEqual(result[5], ["cover-0", "cover-renew-1"])
        self.assertEqual(result[6], {"status": "accepted", "response": accepted})
        self.assertEqual(planner.interrupted, [handle])
        self.assertEqual(json.loads(process.stdin.writes[0]),
                         {"op": "cancel", "id": "cover-renew-1"})

    def test_rejected_invalidated_renewal_interrupts_without_cancel_or_new_terminal(self):
        invalidation = {"reason": "health_below_floor", "sequence": 19}
        prior_terminal = {"event": "terminal", "id": "cover-0", "status": "expired",
                          "release": {"verified": True, "keys_down": [],
                                      "buttons_down": []}}

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
        rejected = {"event": "rejected",
                    "reason": "latest observation sequence required before input"}
        waits = []

        def wait(predicate):
            waits.append(rejected)
            self.assertTrue(predicate(rejected))
            return rejected

        cover_terminals = [prior_terminal]
        cover_ids = ["cover-0"]
        result = extract_renewal_invalidation_branch()(
            {"event": "policy_invalidation", "invalidation": invalidation},
            "cover-renew-1", planner, handle, process, wait, cover_terminals,
            cover_ids, "cover-0", prior_terminal)

        self.assertEqual(result[:2], (invalidation, "cover-0"))
        self.assertEqual(result[2], {"status": "interrupted"})
        self.assertIs(result[3], prior_terminal)
        self.assertEqual(result[4], [prior_terminal])
        self.assertEqual(result[5], ["cover-0"])
        self.assertEqual(result[6], {"status": "rejected", "response": rejected})
        self.assertEqual(planner.interrupted, [handle])
        self.assertEqual(waits, [rejected])
        self.assertEqual(process.stdin.writes, [])


if __name__ == "__main__":
    unittest.main()
