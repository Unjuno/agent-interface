"""Regression for the v38 rejected-action -> unauthored coast interrupt loop."""
import sys
import unittest
from argparse import Namespace
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "live_control")]
import map01_overlap_controller_v39 as controller


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

    def test_stale_partial_action_does_not_reuse_discarded_remaining_cover(self):
        previous = {"iteration": 1, "model_action_discarded": False,
                    "remaining_action_discarded": True,
                    "executor_preacceptance_rejection": {
                        "reason": "latest observation sequence required before input"},
                    "action": {"state": "active", "next_cover": [
                        {"action": "fire", "extent": "short"}],
                        "next_cover_validity": [{"signal_id": "health",
                            "critical_health_minimum": 35,
                            "maximum_health_loss": 12,
                            "max_source_age_ms": 30000}]}}

        self.assertEqual(controller.reusable_cover([previous]), ([], None, None))

    def test_completed_and_legacy_actions_preserve_authored_cover_reuse(self):
        cover = [{"action": "strafe_left", "extent": "short"}]
        validity = [{"signal_id": "health", "critical_health_minimum": 35,
                     "maximum_health_loss": 12, "max_source_age_ms": 30000}]
        for decision in (
            {"iteration": 2, "model_action_discarded": False,
             "remaining_action_discarded": False,
             "action": {"state": "active", "next_cover": cover,
                        "next_cover_validity": validity}},
            {"iteration": 3, "model_action_discarded": False,
             "action": {"state": "active", "next_cover": cover,
                        "next_cover_validity": validity}},
        ):
            with self.subTest(iteration=decision["iteration"]):
                self.assertEqual(controller.reusable_cover([decision]),
                                 (cover, validity[0], decision["iteration"]))

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
            def interrupt(self, handle, before_transport=None):
                if before_transport is not None: before_transport()
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

    def test_initial_cover_invalidation_cancels_before_planner_and_requires_empty_release(self):
        class Stdin:
            def __init__(self): self.writes = []
            def write(self, value): self.writes.append(value)
            def flush(self): pass
        class Process:
            def __init__(self): self.stdin = Stdin()

        terminal = {"event": "terminal", "id": "cover-0",
                    "status": "cancelled",
                    "release": {"verified": True, "keys_down": [],
                                "buttons_down": []}}
        process = Process()
        result = controller.cancel_initial_cover_before_planner(
            process, lambda predicate: terminal if predicate(terminal) else None,
            "cover-0")

        self.assertIs(result, terminal)
        self.assertIn('"op": "cancel"', process.stdin.writes[0])
        for release in (
            {"verified": False, "keys_down": [], "buttons_down": []},
            {"verified": True, "keys_down": ["W"], "buttons_down": []},
            {"verified": True, "keys_down": [], "buttons_down": ["fire"]},
        ):
            unsafe_terminal = dict(terminal, release=release)
            with self.subTest(release=release), self.assertRaisesRegex(
                    RuntimeError, "allowed status and verified empty release"):
                controller.cancel_initial_cover_before_planner(
                    Process(),
                    lambda predicate: unsafe_terminal if predicate(unsafe_terminal) else None,
                    "cover-0")

    def test_cover_invalidation_receipt_distinguishes_preacceptance_from_cancel(self):
        invalidation = {"event": "paired_signal_invalidation",
                        "reason": "health:below_hard_minimum",
                        "sequence": 12}
        coherent = {"required_after_sequence": 11, "fresh_sequence": 13,
                    "additional_invalidations": []}
        rejected = {"ack": {"event": "rejected", "id": "cover-0"},
                    "submitted_sequence": 11, "invalidation": invalidation,
                    "coherent_source_recovery": coherent}
        accepted = {"ack": {"event": "accepted", "id": "cover-0"},
                    "submitted_sequence": 11, "invalidation": invalidation,
                    "coherent_source_recovery": coherent}
        terminal = {"event": "terminal", "id": "cover-0",
                    "status": "cancelled",
                    "release": {"verified": True, "keys_down": [],
                                "buttons_down": []}}

        before_admission = controller.cover_submission_invalidation_receipt(rejected)
        after_admission = controller.cover_submission_invalidation_receipt(
            accepted, terminal)

        self.assertIsNone(before_admission["cover_cancel_terminal"])
        self.assertEqual(before_admission["ack"]["event"], "rejected")
        self.assertEqual(before_admission["coherent_source_recovery"], coherent)
        self.assertIs(after_admission["cover_cancel_terminal"], terminal)
        self.assertEqual(after_admission["ack"]["event"], "accepted")

    def test_observations_consumed_during_executor_ack_are_replayed_after_admission(self):
        class Monitor:
            event_types = {"typed_observation"}
            def __init__(self): self.seen = []
            def observe(self, row):
                self.seen.append(row["sequence"])
                if row["sequence"] == 12:
                    return {"event": "running_action_invalidation",
                            "reason": "health:below_hard_minimum",
                            "source_event": row}
                return None

        monitor = Monitor()
        consumed = [
            {"event": "typed_observation", "sequence": 12},
            {"event": "accepted", "id": "plan-0"},
        ]

        boundary = controller.replay_action_observations_before_wait(
            consumed, monitor)

        self.assertEqual(boundary["event"], "running_action_invalidation")
        self.assertEqual(monitor.seen, [12])

    def test_soft_ack_observation_is_replayed_without_false_invalidation(self):
        class Monitor:
            event_types = {"typed_observation"}
            def __init__(self): self.seen = []
            def observe(self, row):
                self.seen.append(row["sequence"])
                return None

        monitor = Monitor()
        consumed = [
            {"event": "typed_observation", "sequence": 12},
            {"event": "accepted", "id": "plan-0"},
        ]

        boundary = controller.replay_action_observations_before_wait(
            consumed, monitor)

        self.assertIsNone(boundary)
        self.assertEqual(monitor.seen, [12])

    def test_production_action_ack_replay_follows_guard_admission_before_terminal_wait(self):
        source = Path(controller.__file__).read_text(encoding="utf-8")
        execute = source.index("def execute_segment(")
        ack_buffer = source.index("ack_wait_events=[]", execute)
        accepted_wait = source.index("consumed_events=ack_wait_events", ack_buffer)
        guard_admission = source.index("running_guard.admit_program(", accepted_wait)
        replay = source.index("replay_action_observations_before_wait(", guard_admission)
        terminal_wait = source.index('r["event"]=="terminal"', replay)

        self.assertLess(ack_buffer, accepted_wait)
        self.assertLess(accepted_wait, guard_admission)
        self.assertLess(guard_admission, replay)
        self.assertLess(replay, terminal_wait)

    def test_running_invalidation_accepts_naturally_completed_cover_only_when_neutral(self):
        class Stdin:
            def write(self, value): pass
            def flush(self): pass
        class Process:
            stdin = Stdin()
        class Planner:
            def interrupt(self, handle, before_transport=None):
                if before_transport is not None: before_transport()
                return {"status": "interrupted"}

        def wait_for_matching_terminal(terminal):
            unrelated = dict(terminal, id="other-cover")
            rows = (unrelated, terminal)

            def wait(predicate):
                return next((row for row in rows if predicate(row)), None)

            return wait

        for status in ("completed", "expired"):
            neutral_terminal = {
                "event": "terminal", "id": "cover-0", "status": status,
                "release": {"verified": True, "keys_down": [], "buttons_down": []}}
            result = controller.cancel_invalidated_cover(
                Planner(), object(), Process(), wait_for_matching_terminal(neutral_terminal),
                "cover-0")
            self.assertIs(result[1], neutral_terminal)

            held_terminal = {
                "event": "terminal", "id": "cover-0", "status": status,
                "release": {"verified": True, "keys_down": ["space"], "buttons_down": []}}
            with self.assertRaisesRegex(RuntimeError, "verify empty release"):
                controller.cancel_invalidated_cover(
                    Planner(), object(), Process(), wait_for_matching_terminal(held_terminal),
                    "cover-0")

        for status in ("failed", "needs_decision"):
            terminal = {
                "event": "terminal", "id": "cover-0", "status": status,
                "release": {"verified": True, "keys_down": [], "buttons_down": []}}
            with self.subTest(status=status):
                with self.assertRaisesRegex(RuntimeError, "verify empty release"):
                    controller.cancel_invalidated_cover(
                        Planner(), object(), Process(), wait_for_matching_terminal(terminal),
                        "cover-0")

    def test_running_invalidation_rejects_nonempty_or_unverified_release(self):
        class Stdin:
            def write(self, value): pass
            def flush(self): pass
        class Process:
            stdin = Stdin()
        class Planner:
            def interrupt(self, handle, before_transport=None):
                if before_transport is not None: before_transport()
                return {"status": "interrupted"}
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


if __name__ == "__main__":
    unittest.main()
