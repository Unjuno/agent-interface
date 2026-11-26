import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from unittest.mock import patch
import threading
import time
import sys
import io
from contextlib import redirect_stderr

from map01_cover_cycle_experiment_v1 import split_repeated_cover
from map01_overlap_controller_v39 import (compile_cover, CoverCycleBudgetExhausted,
                                           stop_exhausted_cover_budget, qualify_cycle_terminal,
                                           begin_model_turn, short_primary_for_turn)
from executor_v11 import program_sha256
import map01_overlap_controller_v39 as controller


class CoverCycleExperimentTests(unittest.TestCase):
    def test_short_hint_applies_only_to_first_enabled_turn(self):
        self.assertTrue(short_primary_for_turn(True, 0))
        self.assertFalse(short_primary_for_turn(True, 1))
        self.assertFalse(short_primary_for_turn(False, 0))

    def test_short_hint_cannot_run_without_cycle_safety_gates(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'out'
            argv = ['controller', '--out', str(output), '--model', 'example', '--effort', 'low',
                    '--load-fixture-manifest', str(Path(temporary) / 'fixture.json'),
                    '--measurement-session', '--target-process-identity', '--owned-input-service',
                    '--post-load-clock-gate', '--renewal-passive-observer',
                    '--experimental-short-primary']
            stderr = io.StringIO()
            with patch.object(sys, 'argv', argv), redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as stopped:
                    controller.main()
            self.assertEqual(stopped.exception.code, 2)
            self.assertIn('short-primary experiment requires cover-cycle experiment', stderr.getvalue())
            self.assertFalse(output.exists())

    def test_short_hint_is_opt_in_and_does_not_force_unsafe_action(self):
        planner = SimpleNamespace(begin_turn=Mock())
        with tempfile.TemporaryDirectory() as temporary, \
             patch('map01_overlap_controller_v39.win', return_value='image'):
            root = Path(temporary)
            begin_model_turn(planner, root, root / 'frame.png', [], 100, 50, None, {})
            ordinary = (root / 'prompt.txt').read_text()
            begin_model_turn(planner, root, root / 'frame.png', [], 100, 50, None, {},
                             short_experiment=True)
            experimental = (root / 'prompt.txt').read_text()
        self.assertNotIn('experiment', ordinary.lower())
        self.assertIn('when safe', experimental.lower())
        self.assertIn('do not compromise safety', experimental.lower())
        self.assertIn('threat is visible', experimental.lower())
        self.assertIn('empty cover', experimental.lower())
        self.assertTrue(experimental.startswith(ordinary))

    def test_release_requires_matching_program_owner_and_intent(self):
        steps = [{"op": "hold", "keys": ["a"], "duration_ms": 350},
                 {"op": "coast", "duration_ms": 100, "sample_ms": 250}]
        accepted = {"event": "accepted", "id": "cover-1", "intent_token": "token",
                    "program_sha256": program_sha256(steps)}
        release = {"event": "owner_release", "verified": True, "intent_token": "token",
                   "keys_down": [], "buttons_down": [], "keys_unknown": [], "key_state_errors": []}
        terminal = {"event": "terminal", "id": "cover-1", "status": "completed",
                    "input_owner_id": "owner", "input_owner_generation": 2, "release": release}
        source = {"id": "source-refresh-1", "renewal_owner_id": "owner", "input_owner_generation": 2}
        qualify_cycle_terminal(accepted, terminal, [accepted, terminal], source, steps)
        for bad in ({**terminal, "input_owner_id": "wrong"},
                    {**terminal, "input_owner_generation": 3},
                    {**terminal, "input_owner_generation": False},
                    {**terminal, "release": {**release, "intent_token": "wrong"}}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                qualify_cycle_terminal(accepted, bad, [accepted, bad], source, steps)
        with self.assertRaises(ValueError):
            qualify_cycle_terminal({**accepted, "program_sha256": "wrong"}, terminal,
                                   [accepted, terminal], source, steps)
        admission = {"event": "input_admission", "id": "cover-1", "owner_id": "wrong",
                     "intent_token": "token"}
        with self.assertRaises(ValueError):
            qualify_cycle_terminal(accepted, terminal, [accepted, admission, terminal], source, steps)

    def test_exhaustion_retires_pending_planner_after_verified_release(self):
        terminal = {"event": "terminal", "id": "cover-1-renew-3", "status": "completed",
                    "release": {"event": "owner_release", "verified": True,
                                "keys_down": [], "buttons_down": [], "keys_unknown": [],
                                "key_state_errors": []}}
        planner = SimpleNamespace(invalidate_turn=Mock(return_value={"outcome": "invalidated"}),
                                  abort_pending_turn=Mock(return_value={"outcome": "aborted"}))
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(CoverCycleBudgetExhausted) as caught:
                stop_exhausted_cover_budget(planner, "turn", terminal, Path(temporary))
            planner.invalidate_turn.assert_called_once_with("turn")
            planner.abort_pending_turn.assert_called_once_with()
            self.assertEqual(caught.exception.cycle_budget_receipt["outcome"], "HOLD")

    def test_retirement_still_aborts_when_local_invalidation_fails(self):
        terminal = {"event": "terminal", "id": "cover-1", "status": "completed",
                    "release": {"event": "owner_release", "verified": True,
                                "keys_down": [], "buttons_down": [], "keys_unknown": [],
                                "key_state_errors": []}}
        planner = SimpleNamespace(invalidate_turn=Mock(side_effect=RuntimeError("failed")),
                                  abort_pending_turn=Mock(return_value={"outcome": "aborted"}))
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(CoverCycleBudgetExhausted):
                stop_exhausted_cover_budget(planner, "turn", terminal, Path(temporary))
        planner.abort_pending_turn.assert_called_once_with()

    def test_thread_start_failure_stays_budget_hold(self):
        terminal = {"event": "terminal", "id": "cover-1", "status": "completed",
                    "release": {"event": "owner_release", "verified": True,
                                "keys_down": [], "buttons_down": [], "keys_unknown": [],
                                "key_state_errors": []}}
        planner = SimpleNamespace(invalidate_turn=Mock(), abort_pending_turn=Mock())
        with tempfile.TemporaryDirectory() as temporary:
            with patch("map01_overlap_controller_v39.threading.Thread.start",
                       side_effect=RuntimeError("thread unavailable")):
                with self.assertRaises(CoverCycleBudgetExhausted) as caught:
                    stop_exhausted_cover_budget(planner, "turn", terminal, Path(temporary))
            receipt = caught.exception.cycle_budget_receipt
            self.assertEqual(receipt["retirement"]["outcome"], "unknown")
            self.assertEqual(receipt["retirement"]["reason"], "thread_start_failed")

    def test_unverified_terminal_is_recorded_as_unknown_hold(self):
        terminal = {"event": "terminal", "id": "cover-1", "status": "failed",
                    "release": {"event": "owner_release", "verified": False}}
        planner = SimpleNamespace(invalidate_turn=Mock(return_value={"outcome": "invalidated"}),
                                  abort_pending_turn=Mock(return_value={"outcome": "aborted"}))
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(CoverCycleBudgetExhausted) as caught:
                stop_exhausted_cover_budget(planner, "turn", terminal, Path(temporary),
                                            reason="terminal_release_unverified")
            receipt = caught.exception.cycle_budget_receipt
            self.assertEqual(receipt["physical_input_state"], "unknown")
            self.assertFalse(receipt["terminal"]["release"]["verified"])

    def test_blocked_retirement_does_not_delay_hold_indefinitely(self):
        terminal = {"event": "terminal", "id": "cover-1", "status": "completed",
                    "release": {"event": "owner_release", "verified": True,
                                "keys_down": [], "buttons_down": [], "keys_unknown": [],
                                "key_state_errors": []}}
        gate = threading.Event()
        planner = SimpleNamespace(invalidate_turn=Mock(return_value={"outcome": "invalidated"}),
                                  abort_pending_turn=Mock(side_effect=lambda: gate.wait(3)))
        try:
            with tempfile.TemporaryDirectory() as temporary:
                before = time.perf_counter_ns()
                with self.assertRaises(CoverCycleBudgetExhausted) as caught:
                    stop_exhausted_cover_budget(planner, "turn", terminal, Path(temporary))
                receipt = caught.exception.cycle_budget_receipt
                self.assertEqual(receipt["retirement"]["reason"], "retirement_timeout")
                self.assertGreaterEqual(receipt["observation_ended_ns"], before)
                self.assertGreater(receipt["retirement_observed_ns"] -
                                   receipt["observation_ended_ns"], 400_000_000)
        finally:
            gate.set()

    def test_real_compiler_program_can_be_reconstructed(self):
        commands = [{"action": "strafe_left", "extent": "short"},
                    {"action": "strafe_right", "extent": "short"},
                    {"action": "fire", "extent": "short"}]
        original = compile_cover(commands)
        cycle, count = split_repeated_cover(original, hold_count=len(commands))
        self.assertEqual(cycle * count, original)
        self.assertEqual(sum(step["duration_ms"] for step in original), 10000)

    def test_preserves_exact_compiled_program_and_renewal_budget(self):
        cycle = [{"op": "hold", "keys": ["a"], "duration_ms": 350},
                 {"op": "hold", "keys": ["d"], "duration_ms": 350},
                 {"op": "hold", "keys": ["space"], "duration_ms": 100},
                 {"op": "coast", "duration_ms": 1700, "sample_ms": 250}]
        original = cycle * 4
        selected, maximum_submissions = split_repeated_cover(original, hold_count=3)
        self.assertEqual(selected * maximum_submissions, original)
        self.assertEqual(maximum_submissions, 4)
        selected[0]["keys"].append("x")
        self.assertEqual(original[0]["keys"], ["a"])

    def test_unequal_cycles_and_coast_only_do_not_grant_a_split(self):
        coast = {"op": "coast", "duration_ms": 5000, "sample_ms": 250}
        with self.assertRaises(ValueError):
            split_repeated_cover([coast, coast], hold_count=0)
        altered = [{"op": "hold", "keys": ["a"], "duration_ms": 350},
                   {"op": "coast", "duration_ms": 4650, "sample_ms": 250},
                   {"op": "hold", "keys": ["a"], "duration_ms": 350},
                   {"op": "coast", "duration_ms": 4651, "sample_ms": 250}]
        with self.assertRaises(ValueError):
            split_repeated_cover(altered, hold_count=1)
