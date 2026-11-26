"""Clock qualification and first-input gates with inert engine and X11 fixtures."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from map01_post_load_gate_v1 import PostLoadGate


class Clock:
    ns = 1_000_000_000

    def __call__(self):
        return self.ns

    def sleep(self, seconds):
        self.ns += int(seconds * 1e9)


class Game:
    def __init__(self, clock, *, running=True):
        self.clock, self.running = clock, running
        self.tic, self.previous = 1263, clock()
        self.advances = []

    def get_episode_time(self): return self.tic
    def get_ticrate(self): return 35
    def get_episode_timeout(self): return 2625
    def get_mode(self): return "Mode.ASYNC_SPECTATOR"
    def is_player_dead(self): return False
    def is_episode_finished(self): return False
    def is_episode_timeout_reached(self): return False
    def get_last_action(self): return [0] * 9

    def advance_action(self, n, update):
        self.advances.append((n, update))
        current = self.clock()
        self.tic += n + (int((current - self.previous) * 35 / 1e9) if self.running else 0)
        self.previous = current


class PostLoadGateTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.game = Game(self.clock)
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)
        self.display = Mock(return_value={"display": ":120", "xvfb_pid": 7})
        self.neutral = Mock(return_value=True)
        self.gate = PostLoadGate(self.output, 75, clock=self.clock, sleep=self.clock.sleep,
                                 display_proof=self.display, neutral=self.neutral)
        self.session = SimpleNamespace(name=":120")
        self.terminal = {"id": "cover-0", "status": "completed", "input_owner_generation": 1,
                         "input_owner_id": "owner-a",
                         "release": dict(event="owner_release", reason="release", verified=True,
                                         intent_token=None, keys_down=[], buttons_down=[],
                                         keys_unknown=[], key_state_errors=[])}
        self.accepted = {"id": "cover-0", "intent_token": "lease-a"}
        self.source = {"sequence": 2, "capture_ns": self.clock(),
                       "input_owner_generation": 1,
                       "target_process_identity": {"sequence": 2, "surface": 7, "digest": "f" * 64},
                       "pointer_binding": {"focus": 7, "surface": 7, "geometry": [0, 0, 640, 480]}}
        self.owner_state = Mock(return_value={
            "owner_id": "owner-a", "owned_keycodes": [], "owned_buttons": [],
            "active_lease_deadline_ns": None, "release_pending": False, "cancel_requested": False,
            "physical_pointer_mask": 0, "focus": 7, "sample_started_ns": self.clock(),
            "sample_finished_ns": self.clock()})
        self.backend = SimpleNamespace(
            _owner_generation=1, _source_identity=(2, 7, "f"*64), sequence=2,
            owner=SimpleNamespace(owner_id="owner-a", service_id="service",
                                  obligation_snapshot=lambda: None, call=self.owner_state),
            owned_service=SimpleNamespace(service_id="service",
                startup={"display": ":120", "owner_id": "owner-a"},
                process=SimpleNamespace(pid=8, poll=lambda: None)))

    def qualify(self):
        return self.gate.after_load(self.game, self.session, expected_tic=1263)

    def submit(self, identifier, op, *, terminal=None, accepted=None):
        self.source["capture_ns"] = self.clock()
        self.owner_state.return_value.update(
            sample_started_ns=self.clock(), sample_finished_ns=self.clock())
        return self.gate.check_submit(
            {"id": identifier, "expected_sequence": 2, "steps": [{"op": op}]},
            self.backend, self.source, terminal=terminal, accepted=accepted)

    def test_equal_refresh_gate_and_first_hold_have_distinct_freshness(self):
        evidence = self.qualify()
        self.assertTrue(evidence["passed"])
        self.assertEqual(self.game.advances, [(1, True)] * 4)
        self.assertEqual(self.submit("source-refresh-0", "observe"), None)
        self.assertGreater(self.submit("cover-0", "coast"), self.clock())
        self.gate.record({"event": "accepted", **self.accepted})
        self.clock.sleep(12)
        deadline = self.submit("action-0", "hold", terminal=self.terminal, accepted=self.accepted)
        self.assertGreater(deadline, self.clock())
        self.assertEqual(self.game.advances, [(1, True)] * 4)
        self.gate.record({"event": "accepted", "id": "action-0", "intent_token": "lease-first"})
        self.gate.record({"event": "input_admission", "id": "action-0", "owner_id": "owner-a",
                          "intent_token": "lease-first",
                          "first_press_deadline_ns": deadline,
                          "first_press_submission_checked_before_deadline": True,
                          "admitted_ns": self.clock(), "input_ack_ns": self.clock()})
        self.assertIsNone(self.submit("action-1", "hold"))
        rows = [json.loads(line) for line in (self.output / "post-load-clock-gate.jsonl").read_text().splitlines()]
        self.assertEqual(sum(row["event"] == "refresh" for row in rows), 4)

    def accept_initial_cover(self):
        self.qualify()
        self.submit("cover-0", "coast")
        self.gate.record({"event": "accepted", **self.accepted})

    def test_refuses_initial_hold_after_projected_reserve_expires_with_stale_tic(self):
        self.accept_initial_cover()
        last_tic = self.game.get_episode_time()
        self.clock.sleep(60)
        self.assertEqual(self.game.get_episode_time(), last_tic)
        with self.assertRaisesRegex(ValueError, "clock reserve"):
            self.submit("action-0", "hold", terminal=self.terminal, accepted=self.accepted)
        self.assertIsNone(self.gate.first_press)

    def test_refuses_initial_hold_with_less_than_fifteen_game_seconds_left(self):
        self.accept_initial_cover()
        self.game.tic = 2400
        with self.assertRaisesRegex(ValueError, "clock reserve"):
            self.submit("action-0", "hold", terminal=self.terminal, accepted=self.accepted)
        self.assertIsNone(self.gate.first_press)

    def test_near_clock_reserve_limits_the_owner_first_press_deadline(self):
        self.accept_initial_cover()
        last_observed = self.clock()
        self.clock.sleep(16.5)
        deadline = self.submit("action-0", "hold", terminal=self.terminal, accepted=self.accepted)
        wall_deadline = last_observed + (2625 - 1337 - 15 * 35) * 1_000_000_000 // 45
        self.assertEqual(deadline, wall_deadline)
        self.assertGreater(deadline, self.clock())
        self.assertLess(deadline, self.clock() + 1_000_000_000)
        self.assertEqual(self.game.advances, [(1, True)] * 4)

    def test_refuses_stationary_clock_and_held_input(self):
        self.game.running = False
        with self.assertRaisesRegex(ValueError, "clock"):
            self.qualify()
        self.assertEqual(self.game.advances, [(1, True)] * 4)
        with TemporaryDirectory() as output:
            gate = PostLoadGate(Path(output), 75, clock=self.clock, sleep=self.clock.sleep,
                                display_proof=self.display, neutral=lambda _session: False)
            game = Game(self.clock)
            with self.assertRaisesRegex(ValueError, "neutral"):
                gate.after_load(game, self.session, expected_tic=1263)
            self.assertEqual(game.advances, [])

    def test_stale_initial_and_wrong_first_owner_or_release_are_refused(self):
        self.qualify()
        with self.assertRaises(ValueError):
            self.submit("cover-0", "hold")
        self.submit("cover-0", "coast")
        self.gate.record({"event": "accepted", **self.accepted})
        for changed in (
                {**self.terminal, "input_owner_id": "owner-b"},
                {**self.terminal, "input_owner_generation": 2},
                {**self.terminal, "release": {**self.terminal["release"], "intent_token": "wrong"}},
                {**self.terminal, "release": {**self.terminal["release"], "keys_unknown": [38]}},
        ):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                self.submit("action-0", "hold", terminal=changed, accepted=self.accepted)
        self.owner_state.return_value["release_pending"] = True
        with self.assertRaisesRegex(ValueError, "owner"):
            self.submit("action-0", "hold", terminal=self.terminal, accepted=self.accepted)
        self.clock.sleep(2)
        self.gate.initial_cover_accepted = False
        with self.assertRaisesRegex(ValueError, "stale"):
            self.submit("cover-0", "coast")
