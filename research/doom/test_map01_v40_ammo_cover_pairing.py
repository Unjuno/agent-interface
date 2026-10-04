"""Focused tests for the additive V40 paired health/ammo cover guard."""
import ast
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "live_control"))
from observable_signal_guard_v2 import ObservableSignalGuard, ObservableSignalPolicyMonitor


def load_candidate_symbols():
    source = (HERE / "map01_overlap_controller_v40.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    wanted = {"UnauthoredCoastMonitor", "guard_spec", "cover_uses_fire",
              "paired_signal_row", "PairedCoverMonitor", "build_cover_monitor",
              "admitted_cover_commands", "select_cover_monitor",
              "cancel_invalidated_cover"}
    nodes = [node for node in tree.body
             if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in wanted]
    namespace = {"ObservableSignalGuard": ObservableSignalGuard,
                 "ObservableSignalPolicyMonitor": ObservableSignalPolicyMonitor,
                 "MAX_AUTHORED_HEALTH_LOSS": 20, "json": json}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "v40-selected", "exec"), namespace)
    return namespace


V40 = load_candidate_symbols()


class Reader:
    def __init__(self, signal_id):
        self.signal_id = signal_id

    def read(self, observation):
        return observation["signals"][self.signal_id]


class FakeProcess:
    class Stdin:
        def __init__(self):
            self.writes = []
            self.flushed = False

        def write(self, value):
            self.writes.append(value)

        def flush(self):
            self.flushed = True

    def __init__(self):
        self.stdin = self.Stdin()


class FakePlanner:
    def __init__(self):
        self.interrupted = []

    def interrupt(self, handle):
        self.interrupted.append(handle)
        return {"status": "interrupted", "handle": handle}


def signal(signal_id, value, sequence, capture_ns, binding=None):
    return {"format": "observable-signal-v1", "status": "observed",
            "signal_id": signal_id, "value": value, "sequence": sequence,
            "capture_ns": capture_ns,
            "binding": binding or {"session": "synthetic", "surface": 1}}


def observation(sequence, capture_ns, health=100, ammo=4, binding=None):
    binding = binding or {"session": "synthetic", "surface": 1}
    return {"sequence": sequence, "capture_ns": capture_ns, "pointer_binding": binding,
            "signals": {"health": signal("health", health, sequence, capture_ns, binding),
                        "ammo": signal("ammo", ammo, sequence, capture_ns, binding)}}


class V40AmmoCoverPairTests(unittest.TestCase):
    def setUp(self):
        self.health_reader = Reader("health")
        self.ammo_reader = Reader("ammo")
        self.source = observation(10, 1_000_000_000)
        self.fire = [{"action": "fire", "extent": "short"}]
        self.validity = {"signal_id": "health", "critical_health_minimum": 40,
                         "maximum_health_loss": 20, "max_source_age_ms": 30000}

    def monitor(self, source=None, commands=None):
        return V40["build_cover_monitor"](
            self.health_reader, source or self.source, self.validity, 3,
            ammo_reader=self.ammo_reader,
            commands=self.fire if commands is None else commands)

    def test_fire_cover_preserves_positive_ammo_and_tracks_soft_changes(self):
        monitor, receipt = self.monitor()
        self.assertEqual(receipt["monitored_signals"], ["health", "ammo"])
        self.assertIsInstance(monitor, V40["PairedCoverMonitor"])
        self.assertIsNone(monitor.observe(observation(11, 2_000_000_000, health=99, ammo=1)))
        self.assertEqual(monitor.ammo_soft_event_count, 1)
        self.assertEqual(monitor.soft_event_count, 1)
        self.assertEqual(monitor.latest_soft_event["signal_id"], "health")
        self.assertEqual(monitor.latest_ammo_soft_event["signal_id"], "ammo")

    def test_zero_ammo_invalidates_fire_cover(self):
        monitor, _ = self.monitor()
        event = monitor.observe(observation(11, 2_000_000_000, ammo=0))
        self.assertTrue(event["requires_new_decision"])
        self.assertFalse(event["grants_input_authority"])
        self.assertEqual(event["event"]["outcomes"]["ammo"]["status"], "HARD_INVALIDATED")

    def test_ammo_invalidation_flows_through_cancel_and_release_verification(self):
        monitor, _ = self.monitor()
        invalidation = monitor.observe(observation(11, 2_000_000_000, ammo=0))
        boundary = {"event": "policy_invalidation", "invalidation": invalidation}
        self.assertEqual(boundary["event"], "policy_invalidation")
        planner, process = FakePlanner(), FakeProcess()
        terminal = {"event": "terminal", "id": "cover-1", "status": "cancelled",
                    "release": {"verified": True, "buttons_down": [], "keys_down": []}}
        planner_interrupt, observed = V40["cancel_invalidated_cover"](
            planner, "turn-1", process, lambda predicate: terminal if predicate(terminal) else None,
            "cover-1")
        self.assertEqual(planner_interrupt["status"], "interrupted")
        self.assertEqual(planner.interrupted, ["turn-1"])
        self.assertEqual(observed, terminal)
        self.assertEqual(json.loads(process.stdin.writes[0]),
                         {"op": "cancel", "id": "cover-1"})
        self.assertTrue(process.stdin.flushed)

        terminal["release"]["keys_down"] = ["space"]
        with self.assertRaisesRegex(RuntimeError, "did not verify empty release"):
            V40["cancel_invalidated_cover"](
                planner, "turn-2", process,
                lambda predicate: terminal if predicate(terminal) else None, "cover-1")

    def test_split_epoch_unknown_and_bad_value_types_invalidate(self):
        cases = []
        current = observation(11, 2_000_000_000)
        current["signals"]["ammo"]["sequence"] = 12
        cases.append(("sequence mismatch", current))
        current = observation(11, 2_000_000_000)
        current["signals"]["ammo"]["capture_ns"] += 1
        cases.append(("capture mismatch", current))
        current = observation(11, 2_000_000_000)
        current["signals"]["ammo"]["binding"] = {"session": "other", "surface": 1}
        cases.append(("binding mismatch", current))
        current = observation(11, 2_000_000_000)
        current["signals"]["ammo"]["status"] = "unknown"
        cases.append(("unknown ammo", current))
        current = observation(11, 2_000_000_000)
        current["signals"]["ammo"]["sequence"] = True
        cases.append(("boolean sequence", current))
        current = observation(11, 2_000_000_000)
        current["signals"]["ammo"]["sequence"] = 11.0
        cases.append(("float sequence", current))
        current = observation(11, 2_000_000_000)
        current["signals"]["ammo"]["value"] = 4.0
        cases.append(("float value", current))
        current = observation(11, 2_000_000_000)
        current["signals"]["ammo"]["value"] = True
        cases.append(("boolean value", current))
        current = observation(11, 31_001_000_000)
        cases.append(("expired source", current))
        for name, current in cases:
            monitor, _ = self.monitor()
            with self.subTest(name=name):
                self.assertIsNotNone(monitor.observe(current))

    def test_duplicate_or_non_integer_observation_sequence_invalidates(self):
        for sequence in (10, True, 11.0):
            with self.subTest(sequence=sequence):
                monitor, _ = self.monitor()
                current = observation(sequence, 2_000_000_000)
                self.assertIsNotNone(monitor.observe(current))

    def test_signal_pair_must_match_outer_observation_epoch(self):
        current = observation(11, 2_000_000_000)
        current["capture_ns"] += 1
        monitor, _ = self.monitor()
        event = monitor.observe(current)
        self.assertEqual(event["reason"], "signal_observation_epoch_mismatch")

        current = observation(11, 2_000_000_000)
        current["pointer_binding"] = {"session": "other", "surface": 1}
        monitor, _ = self.monitor()
        self.assertEqual(monitor.observe(current)["reason"],
                         "signal_observation_epoch_mismatch")

    def test_nonfire_cover_keeps_health_only_policy(self):
        monitor, receipt = self.monitor(commands=[{"action": "forward", "extent": "short"}])
        self.assertIsInstance(monitor, ObservableSignalPolicyMonitor)
        self.assertEqual(receipt["monitored_signals"], ["health"])
        self.assertIsNone(monitor.observe(observation(11, 2_000_000_000, ammo=0)))

    def test_empty_source_ammo_rejects_fire_commands(self):
        source = observation(10, 1_000_000_000, ammo=0)
        monitor, receipt = self.monitor(source)
        self.assertEqual(receipt["status"], "rejected_source_ammo_empty")
        self.assertEqual(V40["admitted_cover_commands"](self.fire, receipt), [])
        selected, receipt = V40["select_cover_monitor"](
            monitor, receipt, [], 2)
        self.assertIsInstance(selected, V40["UnauthoredCoastMonitor"])
        self.assertEqual(receipt["monitor_mode"], "fire_cover_rejected_empty_coast")

    def test_fire_source_requires_coherent_pair(self):
        source = observation(10, 1_000_000_000)
        source["signals"]["ammo"]["capture_ns"] += 1
        monitor, receipt = self.monitor(source)
        self.assertEqual(receipt["status"], "rejected_source_pair_unavailable")
        self.assertEqual(V40["admitted_cover_commands"](self.fire, receipt), [])
        selected, receipt = V40["select_cover_monitor"](
            monitor, receipt, [], 2)
        self.assertIsInstance(selected, V40["UnauthoredCoastMonitor"])
        self.assertEqual(receipt["monitor_mode"], "fire_cover_rejected_empty_coast")


if __name__ == "__main__":
    unittest.main()
