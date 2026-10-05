"""Regression tests for paired health/ammo invalidation of fire cover."""
import ast
import hashlib
import inspect
import queue
import sys
import time
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "live_control")]
import map01_overlap_controller_v39 as controller


def signal(name, value, sequence=10, capture_ns=1_000_000_000, binding=None):
    return {
        "format": "observable-signal-v1", "status": "observed",
        "signal_id": name, "value": value, "sequence": sequence,
        "capture_ns": capture_ns,
        "binding": binding or {"focus": 7, "surface": 9,
                               "geometry": [0, 0, 640, 480]},
    }


def observation(sequence=10, capture_ns=1_000_000_000, binding=None):
    return {"event": "observation", "sequence": sequence,
            "capture_ns": capture_ns,
            "pointer_binding": binding or {"focus": 7, "surface": 9,
                                            "geometry": [0, 0, 640, 480]}}


class Reader:
    def __init__(self, signal_id, rows):
        self.signal_id = signal_id
        self.rows = rows

    def read(self, row):
        return self.rows[row["sequence"]]


class _WaitProcess:
    def poll(self):
        return None


def _controller_wait_with_rows(rows, handle=None, planner=None):
    """Execute the controller's exact nested wait() dispatch with queued rows."""
    tree = ast.parse(inspect.getsource(controller))
    waits = [node for node in ast.walk(tree)
             if isinstance(node, ast.FunctionDef) and node.name == "wait"]
    if len(waits) != 1:
        raise AssertionError(f"expected one controller wait(), found {len(waits)}")
    factory = ast.parse("""def make_wait(rows, handle, planner):
    incoming = queue.Queue()
    process = _WaitProcess()
    latest = None
    active_turn_handle = handle
    active_decision_index = 0
    active_observation_delivery = None
    for row in rows:
        incoming.put(row)
""").body[0]
    factory.body.extend([
        waits[0],
        ast.Assign(targets=[ast.Attribute(value=ast.Name(id="wait", ctx=ast.Load()),
                                          attr="active_observation_delivery",
                                          ctx=ast.Store())],
                   value=ast.Lambda(args=ast.arguments(posonlyargs=[], args=[],
                                                      kwonlyargs=[], kw_defaults=[],
                                                      defaults=[]),
                                    body=ast.Name(id="active_observation_delivery",
                                                  ctx=ast.Load()))),
        ast.Return(value=ast.Name(id="wait", ctx=ast.Load())),
    ])
    namespace = {
        "queue": queue,
        "time": time,
        "_WaitProcess": _WaitProcess,
        "deliver_active_soft_observation": controller.deliver_active_soft_observation,
    }
    tree = ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[]))
    exec(compile(tree, "<controller-wait-dispatch>", "exec"), namespace)
    return namespace["make_wait"](rows, handle, planner)


class PairedCoverGuardTests(unittest.TestCase):

    def test_live_wait_forwards_exact_soft_frame_once_to_planner(self):
        frame = b"\x89PNG\r\n\x1a\nfixture"
        typed = {"event": "typed_observation", "sequence": 10}
        terminal = {"event": "terminal", "id": "cover-1"}
        class Planner:
            def __init__(self): self.calls = []
            def send_external_observation(self, handle, sequence, text, image_url):
                self.calls.append((handle, sequence, text, image_url))
                return {"outcome": "attached", "sequence": sequence,
                        "thread_id": "thread-1", "turn_id": "turn-1"}
        class Monitor:
            event_types = {"typed_observation", "observation"}
            def __init__(self):
                self.latest_soft_event = {"sequence": 10,
                    "signal": {"status": "observed", "signal_id": "health", "value": 80,
                               "sequence": 10, "capture_ns": 1_000_000_000,
                               "binding": {"focus": 7}},
                    "outcome": {"status": "SOFT_CHANGED",
                                "requires_new_decision": False,
                                "grants_input_authority": False}}
            def observe(self, _row): return None
        planner = Planner()
        handle = object()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "current.png"
            path.write_bytes(frame)
            observation = {"event": "observation", "sequence": 10,
                "capture_ns": 1_000_000_000, "pointer_binding": {"focus": 7},
                "image": str(path)}
            wait = _controller_wait_with_rows(
                [typed, observation, dict(observation), terminal], handle, planner)
            result = wait(lambda row: row.get("id") == "cover-1",
                          observation_monitor=Monitor())
        self.assertIs(result, terminal)
        self.assertEqual(len(planner.calls), 1)
        self.assertIs(planner.calls[0][0], handle)
        self.assertEqual(planner.calls[0][1], 10)
        self.assertEqual(wait.active_observation_delivery()["iteration"], 0)
        self.assertEqual(wait.active_observation_delivery()["frame_sha256"],
                         hashlib.sha256(frame).hexdigest())
        self.assertFalse(wait.active_observation_delivery()["input_authority"])

    def test_only_fire_containing_cover_requires_paired_ammo_guard(self):
        self.assertTrue(controller.cover_requires_ammo([
            {"action": "advance_fire", "extent": "short"}]))
        self.assertFalse(controller.cover_requires_ammo([
            {"action": "strafe_left", "extent": "short"}]))

    def make_monitor(self, health_rows, ammo_rows, *, source=None, firing=True):
        source = source or observation()
        health_reader = Reader("health", health_rows)
        ammo_reader = Reader("ammo", ammo_rows)
        authored = {"signal_id": "health", "critical_health_minimum": 35,
                    "maximum_health_loss": 12, "max_source_age_ms": 30000}
        return controller.build_cover_monitor(
            health_reader, source, authored, 0, ammo_reader=ammo_reader,
            requires_ammo=firing)

    def test_zero_ammo_in_same_fresh_frame_invalidates_fire_cover(self):
        baseline = observation()
        source_health = signal("health", 100)
        source_ammo = signal("ammo", 4)
        changed = observation(11, 1_100_000_000)
        health_rows = {10: source_health, 11: signal("health", 100, 11, 1_100_000_000)}
        ammo_rows = {10: source_ammo, 11: signal("ammo", 0, 11, 1_100_000_000)}
        monitor, receipt = self.make_monitor(health_rows, ammo_rows, source=baseline)

        self.assertEqual(receipt["status"], "admitted")
        event = monitor.observe({
            "event": "typed_observation", "sequence": 11,
            "capture_ns": changed["capture_ns"],
            "pointer_binding": changed["pointer_binding"],
            "signals": {"health": health_rows[11], "ammo": ammo_rows[11]},
        })

        self.assertEqual(event["event"], "paired_signal_invalidation")
        self.assertEqual(event["outcomes"]["ammo"]["reason"], "below_hard_minimum")
        self.assertTrue(event["requires_new_decision"])
        self.assertFalse(event["grants_input_authority"])
        planner_result = SimpleNamespace(
            handle=SimpleNamespace(turn_id="planner-turn"),
            status="interrupted", answer_eligible=False)
        admission = controller.final_admission_from_planner_result(
            planner_result, event["outcome_evaluated_ns"], event,
            time.perf_counter_ns() + 1_000)
        self.assertEqual(admission["status"], "REJECTED_POLICY_INVALIDATED")

    def test_positive_ammo_decrease_is_retained_as_soft_cover_feedback(self):
        monitor, _ = self.make_monitor(
            {10: signal("health", 100),
             11: signal("health", 100, 11, 1_100_000_000)},
            {10: signal("ammo", 4),
             11: signal("ammo", 2, 11, 1_100_000_000)})
        event = monitor.observe({
            "event": "typed_observation", "sequence": 11,
            "capture_ns": 1_100_000_000,
            "pointer_binding": signal("health", 100)["binding"],
            "signals": {"health": signal("health", 100, 11, 1_100_000_000),
                        "ammo": signal("ammo", 2, 11, 1_100_000_000)},
        })

        self.assertIsNone(event)
        summary = controller.latest_soft_event_summary([{
            "iteration": 0, "cover_policy_source_iteration": 0,
            "cover_validity_soft_events": monitor.soft_event_count,
            "cover_validity_latest_soft_event": monitor.latest_soft_event,
        }])
        self.assertEqual(summary["signal_id"], "ammo")
        self.assertEqual(summary["current_value"], 2)

    def test_misaligned_health_ammo_epoch_invalidates_before_guard_evaluation(self):
        health = signal("health", 100, 11, 1_100_000_000)
        ammo = signal("ammo", 4, 10, 1_000_000_000)
        monitor, _ = self.make_monitor(
            {10: signal("health", 100), 11: health},
            {10: signal("ammo", 4), 11: ammo})

        event = monitor.observe({
            "event": "typed_observation", "sequence": 11,
            "capture_ns": 1_100_000_000,
            "pointer_binding": health["binding"],
            "signals": {"health": health, "ammo": ammo},
        })

        self.assertEqual(event["event"], "paired_signal_invalidation")
        self.assertEqual(event["reason"], "signal_pair_epoch_mismatch")
        self.assertTrue(event["requires_new_decision"])

    def test_capture_or_binding_mismatch_invalidates_fire_cover(self):
        monitor, _ = self.make_monitor(
            {10: signal("health", 100), 11: signal("health", 100, 11, 1_100_000_000)},
            {10: signal("ammo", 4), 11: signal("ammo", 4, 11, 1_100_000_000)})
        health = signal("health", 100, 11, 1_100_000_000)
        cases = (
            ("capture", signal("ammo", 4, 11, 1_100_000_001)),
            ("binding", signal("ammo", 4, 11, 1_100_000_000,
                               {"focus": 7, "surface": 10,
                                "geometry": [0, 0, 640, 480]})),
        )
        for name, ammo in cases:
            with self.subTest(identity=name):
                event = monitor.observe({
                    "event": "typed_observation", "sequence": 11,
                    "capture_ns": 1_100_000_000,
                    "pointer_binding": health["binding"],
                    "signals": {"health": health, "ammo": ammo},
                })
                self.assertEqual(event["reason"], "signal_pair_epoch_mismatch")

    def test_boolean_or_float_signal_epoch_alias_invalidates_pair(self):
        monitor, _ = self.make_monitor(
            {10: signal("health", 100), 11: signal("health", 100, 11, 1_100_000_000)},
            {10: signal("ammo", 4), 11: signal("ammo", 4, 11, 1_100_000_000)})
        health = signal("health", 100, 11, 1_100_000_000)
        for field, alias in (("sequence", 11.0), ("capture_ns", 1_100_000_000.0)):
            with self.subTest(field=field):
                ammo = signal("ammo", 4, 11, 1_100_000_000)
                ammo[field] = alias
                event = monitor.observe({
                    "event": "typed_observation", "sequence": 11,
                    "capture_ns": 1_100_000_000,
                    "pointer_binding": health["binding"],
                    "signals": {"health": health, "ammo": ammo},
                })
                self.assertEqual(event["reason"], "signal_pair_epoch_mismatch")

    def test_boolean_observation_sequence_is_rejected_as_invalid_pair(self):
        monitor, _ = self.make_monitor(
            {10: signal("health", 100), 11: signal("health", 100, 11, 1_100_000_000)},
            {10: signal("ammo", 4), 11: signal("ammo", 4, 11, 1_100_000_000)})
        event = monitor.observe({
            "event": "typed_observation", "sequence": True,
            "capture_ns": 1_100_000_000,
            "pointer_binding": signal("health", 100)["binding"],
            "signals": {"health": signal("health", 100, 1, 1_100_000_000),
                        "ammo": signal("ammo", 4, 1, 1_100_000_000)},
        })
        self.assertEqual(event["reason"], "signal_pair_epoch_mismatch")

    def test_out_of_order_pair_after_valid_sample_invalidates_fire_cover(self):
        monitor, _ = self.make_monitor(
            {10: signal("health", 100), 11: signal("health", 100, 11, 1_100_000_000)},
            {10: signal("ammo", 4), 11: signal("ammo", 4, 11, 1_100_000_000)})
        for sequence in (12, 11):
            observation_ns = sequence * 100_000_000
            signals = {name: signal(name, value, sequence, observation_ns)
                       for name, value in (("health", 100), ("ammo", 4))}
            event = monitor.observe({
                "event": "typed_observation", "sequence": sequence,
                "capture_ns": observation_ns,
                "pointer_binding": signals["health"]["binding"],
                "signals": signals,
            })
        self.assertEqual(event["reason"], "signal_pair_nonadvancing_sequence")

    def test_capture_timestamp_must_advance_with_sequence(self):
        monitor, _ = self.make_monitor(
            {10: signal("health", 100), 11: signal("health", 100, 11, 1_100_000_000)},
            {10: signal("ammo", 4), 11: signal("ammo", 4, 11, 1_100_000_000)})
        for sequence, capture_ns in ((12, 1_200_000_000), (13, 1_150_000_000)):
            signals = {
                "health": signal("health", 100, sequence, capture_ns),
                "ammo": signal("ammo", 4, sequence, capture_ns),
            }
            event = monitor.observe({
                "event": "typed_observation", "sequence": sequence,
                "capture_ns": capture_ns,
                "pointer_binding": signals["health"]["binding"],
                "signals": signals,
            })
        self.assertEqual(event["reason"], "signal_pair_nonadvancing_capture_time")

    def test_source_binding_bool_integer_alias_is_rejected(self):
        binding_int = {"focus": 1, "surface": 9, "geometry": [0, 0, 640, 480]}
        binding_bool = {"focus": True, "surface": 9, "geometry": [0, 0, 640, 480]}
        source = observation(binding=binding_int)
        health = signal("health", 100, binding=binding_int)
        ammo = signal("ammo", 4, binding=binding_bool)
        monitor, receipt = self.make_monitor(
            {10: health}, {10: ammo}, source=source)
        self.assertEqual(receipt["status"], "rejected_source_health_ammo_pair")
        self.assertEqual(controller.admitted_cover_commands(
            [{"action": "fire", "extent": "short"}], receipt), [])

    def test_current_binding_bool_integer_alias_invalidates_pair(self):
        binding_int = {"focus": 1, "surface": 9, "geometry": [0, 0, 640, 480]}
        monitor, _ = self.make_monitor(
            {10: signal("health", 100, binding=binding_int),
             11: signal("health", 100, 11, 1_100_000_000, binding_int)},
            {10: signal("ammo", 4, binding=binding_int),
             11: signal("ammo", 4, 11, 1_100_000_000, binding_int)},
            source=observation(binding=binding_int))
        health = signal("health", 100, 11, 1_100_000_000, binding_int)
        ammo_binding = {"focus": True, "surface": 9, "geometry": [0, 0, 640, 480]}
        ammo = signal("ammo", 4, 11, 1_100_000_000, ammo_binding)
        event = monitor.observe({
            "event": "typed_observation", "sequence": 11,
            "capture_ns": 1_100_000_000,
            "pointer_binding": health["binding"],
            "signals": {"health": health, "ammo": ammo},
        })
        self.assertEqual(event["reason"], "signal_pair_epoch_mismatch")

    def test_full_observation_without_typed_companion_is_dispatched(self):
        source = observation()
        next_observation = observation(11, 1_100_000_000)
        health_rows = {10: signal("health", 100),
                       11: signal("health", 100, 11, 1_100_000_000)}
        ammo_rows = {10: signal("ammo", 4),
                     11: signal("ammo", 0, 11, 1_100_000_000)}
        monitor, _ = self.make_monitor(health_rows, ammo_rows, source=source)

        wait = _controller_wait_with_rows([next_observation])
        event = wait(lambda row: row["event"] == "observation",
                     timeout=0.2, observation_monitor=monitor)

        self.assertEqual(event["event"], "policy_invalidation")
        self.assertEqual(event["invalidation"]["event"], "paired_signal_invalidation")
        self.assertEqual(event["invalidation"]["outcomes"]["ammo"]["reason"],
                         "below_hard_minimum")

    def test_typed_then_full_duplicate_epoch_is_processed_once(self):
        monitor, _ = self.make_monitor(
            {10: signal("health", 100),
             11: signal("health", 100, 11, 1_100_000_000)},
            {10: signal("ammo", 4),
             11: signal("ammo", 2, 11, 1_100_000_000)})
        health = signal("health", 100, 11, 1_100_000_000)
        ammo = signal("ammo", 2, 11, 1_100_000_000)
        typed = {"event": "typed_observation", "sequence": 11,
                 "capture_ns": 1_100_000_000,
                 "pointer_binding": health["binding"],
                 "frame_rgb_sha256": "a" * 64,
                 "signals": {"health": health, "ammo": ammo}}
        ordinary = {"event": "observation", "sequence": 11,
                    "capture_ns": 1_100_000_000,
                    "pointer_binding": health["binding"],
                    "frame_rgb_sha256": "a" * 64}

        self.assertIn("observation", controller.DoomCoverSignalPairMonitor.event_types)
        self.assertIsNone(monitor.observe(typed))
        self.assertIsNone(monitor.observe(ordinary))
        self.assertEqual(monitor.soft_event_count, 1)

    def test_full_then_typed_duplicate_epoch_is_processed_once(self):
        monitor, _ = self.make_monitor(
            {10: signal("health", 100),
             11: signal("health", 100, 11, 1_100_000_000)},
            {10: signal("ammo", 4),
             11: signal("ammo", 2, 11, 1_100_000_000)})
        health = signal("health", 100, 11, 1_100_000_000)
        ammo = signal("ammo", 2, 11, 1_100_000_000)
        ordinary = {"event": "observation", "sequence": 11,
                    "capture_ns": 1_100_000_000,
                    "pointer_binding": health["binding"],
                    "frame_rgb_sha256": "a" * 64}
        typed = {"event": "typed_observation", "sequence": 11,
                 "capture_ns": 1_100_000_000,
                 "pointer_binding": health["binding"],
                 "frame_rgb_sha256": "a" * 64,
                 "signals": {"health": health, "ammo": ammo}}

        self.assertIsNone(monitor.observe(ordinary))
        self.assertIsNone(monitor.observe(typed))
        self.assertEqual(monitor.soft_event_count, 1)

    def test_full_observation_reader_error_invalidates_instead_of_escaping(self):
        class FailedReader:
            def read(self, _observation):
                raise OSError("fixture image unavailable")

        monitor, _ = self.make_monitor(
            {10: signal("health", 100),
             11: signal("health", 100, 11, 1_100_000_000)},
            {10: signal("ammo", 4),
             11: signal("ammo", 4, 11, 1_100_000_000)})
        monitor.readers["ammo"] = FailedReader()

        event = monitor.observe(observation(11, 1_100_000_000))

        self.assertEqual(event["reason"], "signal_pair_source_unavailable")
        self.assertTrue(event["requires_new_decision"])

    def test_nonfire_cover_keeps_health_only_monitor(self):
        source = observation()
        health = signal("health", 100)
        monitor, receipt = self.make_monitor(
            {10: health}, {}, source=source, firing=False)

        self.assertIsInstance(monitor, controller.ObservableSignalPolicyMonitor)
        self.assertEqual(receipt["status"], "admitted")

    def test_fire_cover_refuses_unavailable_source_ammo(self):
        unknown = {"status": "unknown", "signal_id": "ammo", "value": None,
                   "sequence": 10, "capture_ns": 1_000_000_000,
                   "binding": signal("health", 100)["binding"]}
        monitor, receipt = self.make_monitor(
            {10: signal("health", 100)}, {10: unknown})
        self.assertEqual(receipt["status"], "rejected_source_health_ammo_pair")
        self.assertEqual(controller.admitted_cover_commands(
            [{"action": "fire", "extent": "short"}], receipt), [])
        self.assertFalse(receipt["grants_input_authority"])

    def test_fire_cover_refuses_source_signals_from_different_observations(self):
        older_ammo = signal("ammo", 4, 9, 900_000_000)
        monitor, receipt = self.make_monitor(
            {10: signal("health", 100)}, {10: older_ammo})
        self.assertEqual(receipt["status"], "rejected_source_health_ammo_pair")
        self.assertEqual(controller.admitted_cover_commands(
            [{"action": "fire", "extent": "short"}], receipt), [])


    def test_current_action_admission_rejects_float_epoch_metadata(self):
        binding = {"focus": 7, "surface": 9, "geometry": [0, 0, 640, 480]}
        contract = {"source": {"signals": ["health", "ammo"]}}
        command = {"commands": [{"action": "fire", "extent": "short"}]}
        authored = {}
        source_health = signal("health", 100, sequence=3, capture_ns=30, binding=binding)
        source_ammo = signal("ammo", 4, sequence=3, capture_ns=30, binding=binding)
        current_health = signal("health", 100, sequence=4, capture_ns=40, binding=binding)

        for field, alias in (("sequence", 4.0), ("capture_ns", 40.0)):
            with self.subTest(field=field, alias=alias):
                current_ammo = signal("ammo", 2, sequence=4, capture_ns=40,
                                      binding=binding)
                current_ammo[field] = alias
                with patch.object(controller, "build_action_contract",
                                  return_value=contract), \
                     patch.object(controller, "evaluate_action_validity") as evaluate, \
                     patch.object(controller, "record_action_validity") as record:
                    with self.assertRaisesRegex(
                            ValueError, "epoch metadata must be exact integers"):
                        controller.prepare_action_admission(
                            {}, command, authored, source_health, source_ammo,
                            current_health, current_ammo, 41)
                    evaluate.assert_not_called()
                    record.assert_not_called()

        current_ammo = signal("ammo", 2, sequence=4, capture_ns=40,
                              binding=binding)
        validity = {"status": "VALID_CURRENT"}
        with patch.object(controller, "build_action_contract",
                          return_value=contract), \
             patch.object(controller, "evaluate_action_validity",
                          return_value=validity) as evaluate, \
             patch.object(controller, "record_action_validity",
                          return_value=validity):
            result = controller.prepare_action_admission(
                {}, command, authored, source_health, source_ammo,
                current_health, current_ammo, 41)
        self.assertEqual(result["status"], "VALID_CURRENT")
        snapshot = evaluate.call_args.args[2]
        self.assertEqual(snapshot["sequence"], 4)
        self.assertEqual(snapshot["capture_ns"], 40)


if __name__ == "__main__":
    unittest.main()
