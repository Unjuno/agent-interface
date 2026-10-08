"""Regression for observations queued as the planner future completes."""
import queue
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from executor_v12 import Executor as ExecutorV12
from map01_overlap_controller_v39 import (
    MAX_PENDING_OBSERVATION_EVENTS, DoomCoverSignalPairMonitor,
    drain_pending_observation_events, recover_pending_observation_backlog,
    recover_stale_cover_submission, settle_pending_observation_backlog,
    submit_initial_cover_with_recovery)


class Monitor:
    event_types = {"observation", "typed_observation"}

    def __init__(self, invalidate_on=None):
        self.invalidate_on = invalidate_on
        self.seen = []

    def observe(self, row):
        self.seen.append(row["sequence"])
        if row["sequence"] == self.invalidate_on:
            return {"event": "policy_invalidation",
                    "reason": "health:below_hard_minimum",
                    "requires_new_decision": True}
        return None


class SignalGuard:
    def __init__(self, signal_id, source_value, source_sequence,
                 source_capture_ns, hard_minimum):
        self.spec = {"signal_id": signal_id, "source_value": source_value,
                     "source_sequence": source_sequence}
        self.source_capture_ns = source_capture_ns
        self.hard_minimum = hard_minimum

    def evaluate(self, signal):
        invalid = signal["value"] < self.hard_minimum
        changed = signal["value"] != self.spec["source_value"]
        status = ("HARD_INVALIDATED" if invalid else
                  "SOFT_CHANGED" if changed else "UNCHANGED")
        reason = ("below_hard_minimum" if invalid else
                  "within_validity_envelope" if changed else "signal_unchanged")
        return {"status": status,
                "reason": reason,
                "requires_new_decision": invalid}


class SignalReader:
    def read(self, observation):
        return observation["signals"][self.signal_id]

    def __init__(self, signal_id):
        self.signal_id = signal_id


def typed_signal(signal_id, value, sequence, capture_ns, binding):
    return {"status": "observed", "signal_id": signal_id, "value": value,
            "sequence": sequence, "capture_ns": capture_ns,
            "binding": dict(binding)}


class PendingObservationDrainTests(unittest.TestCase):
    def test_stale_initial_cover_observations_are_evaluated_and_cover_is_discarded(self):
        incoming = queue.Queue()
        monitor = Monitor(invalidate_on=12)
        rejected = {"event": "rejected", "id": "cover-0",
                    "reason": "latest observation sequence required before input"}
        consumed = [
            {"event": "observation", "sequence": 11},
            {"event": "typed_observation", "sequence": 12},
        ]
        fresh = {"event": "observation", "sequence": 13, "image": "frame-13"}

        result = recover_stale_cover_submission(
            rejected, identifier="cover-0", expected_sequence=10,
            consumed_events=consumed, latest={"sequence": 10},
            incoming=incoming, wait=lambda predicate: fresh if predicate(fresh) else None,
            observation_monitor=monitor)

        self.assertEqual(monitor.seen, [11, 12])
        self.assertEqual(result["latest"]["sequence"], 13)
        self.assertEqual(result["cover_policy"], "discarded_until_fresh_plan")
        self.assertEqual(result["invalidation"]["reason"], "health:below_hard_minimum")

    def test_stale_initial_cover_uses_pre_submit_sequence_when_ack_updates_latest(self):
        latest = {"sequence": 10}
        events = []
        monitor = Monitor()
        rejected = {"event": "rejected", "id": "cover-0",
                    "reason": "latest observation sequence required before input"}

        def submit(consumed_events):
            rows = [
                {"event": "typed_observation", "sequence": 11},
                {"event": "observation", "sequence": 12, "image": "frame-12"},
            ]
            events.extend(rows)
            consumed_events.extend(rows)
            latest.update(sequence=12, image="frame-12")
            return rejected

        result = submit_initial_cover_with_recovery(
            submit, identifier="cover-0", latest_reader=lambda: latest,
            incoming=queue.Queue(), wait=lambda predicate: self.fail(
                "already received fresh observation must not trigger another wait"),
            observation_monitor=monitor)

        self.assertEqual(result["submitted_sequence"], 10)
        self.assertEqual(result["latest"]["sequence"], 12)
        self.assertEqual(result["ack"], rejected)
        self.assertEqual(monitor.seen, [11, 12])

    def test_reader_lookahead_rows_are_not_mistaken_for_ack_wait_consumption(self):
        binding = {"focus": 7, "surface": 9,
                   "geometry": [0, 0, 640, 480]}
        signals = {
            "health": typed_signal("health", 95, 12, 1_100_000_000, binding),
            "ammo": typed_signal("ammo", 4, 12, 1_100_000_000, binding),
        }
        typed = {"event": "typed_observation", "sequence": 12,
                 "capture_ns": 1_100_000_000, "pointer_binding": binding,
                 "frame_rgb_sha256": "a" * 64, "signals": signals}
        full = dict(typed, event="observation")
        latest = {"sequence": 11}
        event_log = []
        incoming = queue.Queue()
        monitor = DoomCoverSignalPairMonitor(
            {"health": SignalGuard("health", 100, 11, 1_000_000_000, 60),
             "ammo": SignalGuard("ammo", 4, 11, 1_000_000_000, 1)},
            health_reader=SignalReader("health"),
            ammo_reader=SignalReader("ammo"))
        rejected = {"event": "rejected", "id": "cover-0",
                    "reason": "latest observation sequence required before input"}

        def submit(consumed_events):
            # The reader has logged both rows, but the ACK wait only consumed
            # the typed row; the full observation is still in the queue.
            event_log.extend([typed, full])
            consumed_events.append(typed)
            incoming.put(full)
            return rejected

        result = submit_initial_cover_with_recovery(
            submit, identifier="cover-0", latest_reader=lambda: latest,
            incoming=incoming,
            wait=lambda predicate: self.fail("the queued full frame is sufficient"),
            observation_monitor=monitor)

        self.assertIsNone(result["invalidation"])
        self.assertEqual(monitor.soft_event_count, 1)
        self.assertTrue(incoming.empty())

    def test_accepted_initial_cover_ack_observes_hard_crossing_consumed_during_wait(self):
        binding = {"focus": 7, "surface": 9,
                   "geometry": [0, 0, 640, 480]}
        signals = {
            "health": typed_signal("health", 50, 12, 1_100_000_000, binding),
            "ammo": typed_signal("ammo", 4, 12, 1_100_000_000, binding),
        }
        typed = {"event": "typed_observation", "sequence": 12,
                 "capture_ns": 1_100_000_000, "pointer_binding": binding,
                 "frame_rgb_sha256": "a" * 64, "signals": signals}
        full = dict(typed, event="observation")
        latest = {"sequence": 11}
        consumed = []
        monitor = DoomCoverSignalPairMonitor(
            {"health": SignalGuard("health", 100, 11, 1_000_000_000, 60),
             "ammo": SignalGuard("ammo", 4, 11, 1_000_000_000, 1)},
            health_reader=SignalReader("health"),
            ammo_reader=SignalReader("ammo"))

        def submit(consumed_events):
            consumed_events.extend([typed, full])
            consumed.extend([typed, full])
            latest.update(full)
            return {"event": "accepted", "id": "cover-0"}

        result = submit_initial_cover_with_recovery(
            submit, identifier="cover-0", latest_reader=lambda: latest,
            incoming=queue.Queue(), wait=lambda predicate: self.fail("unexpected wait"),
            observation_monitor=monitor)

        self.assertEqual(result["ack"]["event"], "accepted")
        self.assertEqual(result["invalidation"]["reason"],
                         "health:below_hard_minimum")
        self.assertEqual(monitor.last_sequence, 12)
        self.assertEqual(consumed, [typed, full])

    def test_accepted_ack_validates_pair_after_first_hard_half_invalidates(self):
        binding = {"focus": 7, "surface": 9,
                   "geometry": [0, 0, 640, 480]}
        hard_signals = {
            "health": typed_signal("health", 50, 12, 1_100_000_000, binding),
            "ammo": typed_signal("ammo", 4, 12, 1_100_000_000, binding),
        }
        disagreeing_signals = dict(hard_signals)
        disagreeing_signals["health"] = typed_signal(
            "health", 100, 12, 1_100_000_000, binding)
        typed = {"event": "typed_observation", "sequence": 12,
                 "capture_ns": 1_100_000_000, "pointer_binding": binding,
                 "frame_rgb_sha256": "a" * 64, "signals": hard_signals}
        full = dict(typed, event="observation", signals=disagreeing_signals)
        latest = dict(full)
        incoming = queue.Queue()
        fresh_signals = {
            "health": typed_signal("health", 95, 13, 1_200_000_000, binding),
            "ammo": typed_signal("ammo", 4, 13, 1_200_000_000, binding),
        }
        fresh_typed = {"event": "typed_observation", "sequence": 13,
                       "capture_ns": 1_200_000_000,
                       "pointer_binding": binding,
                       "frame_rgb_sha256": "b" * 64,
                       "signals": fresh_signals}
        fresh_full = dict(fresh_typed, event="observation")
        incoming.put(typed)
        incoming.put(fresh_typed)
        incoming.put(fresh_full)
        monitor = DoomCoverSignalPairMonitor(
            {"health": SignalGuard("health", 100, 11, 1_000_000_000, 60),
             "ammo": SignalGuard("ammo", 4, 11, 1_000_000_000, 1)},
            health_reader=SignalReader("health"),
            ammo_reader=SignalReader("ammo"))

        def submit(consumed_events):
            # The reader logs/queues typed first, but the ACK wait consumes
            # only the full row. Pair integrity is discovered during recovery.
            consumed_events.append(full)
            return {"event": "accepted", "id": "cover-0"}

        def wait(predicate, observation_monitor=None):
            while not incoming.empty():
                row = incoming.get_nowait()
                if row["event"] == "observation":
                    latest.update(row)
                if row["event"] in observation_monitor.event_types:
                    observation_monitor.observe(row)
                if predicate(row):
                    return row
            self.fail("coherent post-mismatch pair was not awaited")

        result = submit_initial_cover_with_recovery(
            submit, identifier="cover-0", latest_reader=lambda: latest,
            incoming=incoming, wait=wait,
            observation_monitor=monitor)

        self.assertEqual(result["invalidation"]["reason"],
                         "signal_pair_duplicate_epoch_mismatch")
        self.assertEqual(result["latest"]["sequence"], 13)
        self.assertEqual(result["coherent_source_recovery"]["fresh_sequence"], 13)

    def test_backlog_drain_checks_pair_after_first_hard_half_invalidates(self):
        binding = {"focus": 7, "surface": 9,
                   "geometry": [0, 0, 640, 480]}
        hard_signals = {
            "health": typed_signal("health", 50, 12, 1_100_000_000, binding),
            "ammo": typed_signal("ammo", 4, 12, 1_100_000_000, binding),
        }
        disagreeing_signals = dict(hard_signals)
        disagreeing_signals["health"] = typed_signal(
            "health", 100, 12, 1_100_000_000, binding)
        typed = {"event": "typed_observation", "sequence": 12,
                 "capture_ns": 1_100_000_000, "pointer_binding": binding,
                 "frame_rgb_sha256": "a" * 64, "signals": hard_signals}
        full = dict(typed, event="observation", signals=disagreeing_signals)
        incoming = queue.Queue()
        incoming.put(typed)
        incoming.put(full)
        monitor = DoomCoverSignalPairMonitor(
            {"health": SignalGuard("health", 100, 11, 1_000_000_000, 60),
             "ammo": SignalGuard("ammo", 4, 11, 1_000_000_000, 1)},
            health_reader=SignalReader("health"),
            ammo_reader=SignalReader("ammo"))

        result = drain_pending_observation_events(incoming, monitor, "cover-0")

        self.assertEqual(result["invalidation"]["reason"],
                         "signal_pair_duplicate_epoch_mismatch")
        self.assertTrue(incoming.empty())

    def test_stale_cover_recovery_returns_newer_coherent_pair(self):
        binding = {"focus": 7, "surface": 9,
                   "geometry": [0, 0, 640, 480]}
        signals = {
            "health": typed_signal("health", 50, 12, 1_100_000_000, binding),
            "ammo": typed_signal("ammo", 4, 12, 1_100_000_000, binding),
        }
        typed = {"event": "typed_observation", "sequence": 12,
                 "capture_ns": 1_100_000_000, "pointer_binding": binding,
                 "frame_rgb_sha256": "a" * 64, "signals": signals}
        mismatch_signals = dict(signals)
        mismatch_signals["health"] = typed_signal(
            "health", 100, 12, 1_100_000_000, binding)
        mismatch_full = dict(typed, event="observation", signals=mismatch_signals)
        latest = {"sequence": 12, **mismatch_full}
        incoming = queue.Queue()
        fresh_signals = {
            "health": typed_signal("health", 95, 13, 1_200_000_000, binding),
            "ammo": typed_signal("ammo", 4, 13, 1_200_000_000, binding),
        }
        fresh_typed = {"event": "typed_observation", "sequence": 13,
                       "capture_ns": 1_200_000_000,
                       "pointer_binding": binding,
                       "frame_rgb_sha256": "b" * 64,
                       "signals": fresh_signals}
        incoming.put(fresh_typed)
        incoming.put(dict(fresh_typed, event="observation"))
        monitor = DoomCoverSignalPairMonitor(
            {"health": SignalGuard("health", 100, 11, 1_000_000_000, 60),
             "ammo": SignalGuard("ammo", 4, 11, 1_000_000_000, 1)},
            health_reader=SignalReader("health"),
            ammo_reader=SignalReader("ammo"))
        rejected = {"event": "rejected", "id": "cover-0",
                    "reason": "latest observation sequence required before input"}

        result = recover_stale_cover_submission(
            rejected, identifier="cover-0", expected_sequence=11,
            consumed_events=[typed, mismatch_full], latest=latest,
            latest_reader=lambda: latest, incoming=incoming,
            wait=lambda predicate: self.fail("queued pair should finish recovery"),
            observation_monitor=monitor)

        self.assertEqual(result["invalidation"]["reason"],
                         "signal_pair_duplicate_epoch_mismatch")
        self.assertEqual(result["latest"]["sequence"], 13)
        self.assertEqual(result["coherent_source_recovery"]["fresh_sequence"], 13)

    def test_queued_hard_crossing_precedes_completed_answer(self):
        incoming = queue.Queue()
        incoming.put({"event": "typed_observation", "sequence": 12})
        incoming.put({"event": "terminal", "id": "cover-1",
                      "status": "completed",
                      "release": {"verified": True, "keys_down": [],
                                  "buttons_down": []}})
        monitor = Monitor(invalidate_on=12)

        result = drain_pending_observation_events(incoming, monitor, "cover-1")

        self.assertEqual(monitor.seen, [12])
        self.assertEqual(result["invalidation"]["reason"],
                         "health:below_hard_minimum")
        self.assertEqual(result["terminal"]["status"], "completed")
        self.assertTrue(incoming.empty())

    def test_soft_observation_and_terminal_preserve_completed_answer_path(self):
        incoming = queue.Queue()
        incoming.put({"event": "observation", "sequence": 20})
        incoming.put({"event": "terminal", "id": "cover-2",
                      "status": "completed"})
        monitor = Monitor()

        result = drain_pending_observation_events(incoming, monitor, "cover-2")

        self.assertEqual(result["latest"]["sequence"], 20)
        self.assertIsNone(result["invalidation"])
        self.assertEqual(result["terminal"]["id"], "cover-2")


    def test_completed_future_drain_is_wired_before_answer_read(self):
        source = Path(__file__).with_name("map01_overlap_controller_v39.py").read_text(
            encoding="utf-8")
        loop = source.index("while not future.done():")
        drain = source.index("drain_pending_observation_events(", loop)
        result = source.index("planner_result=future.result()", drain)
        discard = source.index("if invalidation is not None:", result)
        eligible = source.index("if not planner_result.answer_eligible:", discard)
        self.assertLess(loop, drain)
        self.assertLess(drain, result)
        self.assertLess(result, discard)
        self.assertLess(discard, eligible)

    def test_empty_backlog_is_nonblocking_and_returns_no_boundary(self):
        incoming = queue.Queue()
        monitor = Monitor()

        result = drain_pending_observation_events(incoming, monitor, "cover-3")

        self.assertEqual(result, {"latest": None, "terminal": None,
                                  "invalidation": None,
                                  "pending_events": False})
        self.assertEqual(monitor.seen, [])

    def test_bounded_drain_processes_events_arriving_after_entry(self):
        incoming = queue.Queue()
        incoming.put({"event": "observation", "sequence": 30})

        class EnqueueDuringObserve(Monitor):
            enqueued = False

            def observe(self, row):
                self.seen.append(row["sequence"])
                if not self.enqueued:
                    self.enqueued = True
                    incoming.put({"event": "observation", "sequence": 31})
                return None

        monitor = EnqueueDuringObserve()
        result = drain_pending_observation_events(incoming, monitor, "cover-4")

        self.assertEqual(monitor.seen, [30, 31])
        self.assertEqual(result["latest"]["sequence"], 31)
        self.assertFalse(result["pending_events"])
        self.assertTrue(incoming.empty())

    def test_boundary_hard_crossing_is_processed_before_answer_reuse(self):
        incoming = queue.Queue()

        class EnqueueHardCrossingDuringObserve(Monitor):
            def observe(self, row):
                self.seen.append(row["sequence"])
                if row["sequence"] == 11:
                    incoming.put({"event": "typed_observation", "sequence": 12})
                if row["sequence"] == 12:
                    return {"event": "paired_signal_invalidation",
                            "reason": "health:below_hard_minimum",
                            "requires_new_decision": True}
                return None

        incoming.put({"event": "observation", "sequence": 11})
        monitor = EnqueueHardCrossingDuringObserve()
        result = drain_pending_observation_events(incoming, monitor, "cover-race")

        self.assertEqual(monitor.seen, [11, 12])
        self.assertEqual(result["invalidation"]["reason"],
                         "health:below_hard_minimum")
        self.assertFalse(result["pending_events"])
        self.assertTrue(incoming.empty())

        fresh = {"event": "observation", "sequence": 12, "image": "frame-12"}
        waits = []

        def wait(predicate):
            waits.append(predicate(fresh))
            return fresh

        recovery = recover_pending_observation_backlog(
            incoming, result["latest"], 11, "cover-race", wait)

        self.assertEqual(waits, [True])
        self.assertEqual(recovery["fresh_observation_sequence"], 12)
        self.assertIs(recovery["latest"], fresh)

    def test_actual_executor_stale_cover_ack_reuses_observation_received_during_wait(self):
        class Backend:
            sequence = 12
            lease = None

            @staticmethod
            def validate(steps):
                return None

        started = []
        published = []

        class NoInputThread:
            def __init__(self, target, args, daemon):
                self.target = target
                self.args = args
                self.daemon = daemon

            def start(self):
                started.append(self.args[0])

        executor = ExecutorV12.__new__(ExecutorV12)
        executor.lock = threading.RLock()
        executor.closed = False
        executor.active = None
        executor.backend = Backend()
        executor.used_ids = set()
        executor.admission_callback_ids = set()
        executor.terminal_publication_errors = {}
        executor.admission_publication_errors = {}
        executor.emit = published.append
        deadline = time.perf_counter_ns() + 10_000_000_000
        incoming = queue.Queue()
        latest = {"sequence": 11}
        all_events = []
        monitor = Monitor(invalidate_on=12)
        rows = [
            {"event": "typed_observation", "sequence": 12},
            {"event": "observation", "sequence": 12, "image": "frame-12"},
        ]

        def submit_stale_cover(consumed_events):
            with self.assertRaisesRegex(
                    ValueError, "latest observation sequence required before input"):
                executor.submit("stale-plan", [{"op": "observe"}], 11, deadline)
            # The controller's ordinary ACK wait drains these rows before the
            # adapter presents the matching stale rejection to the caller.
            while rows:
                row = rows.pop(0)
                all_events.append(row)
                consumed_events.append(row)
                if row["event"] == "observation":
                    latest.update(row)
            return {"event": "rejected", "id": "stale-plan",
                    "reason": "latest observation sequence required before input"}

        with patch("executor_v12.threading.Thread", NoInputThread):
            recovered = submit_initial_cover_with_recovery(
                submit_stale_cover, identifier="stale-plan",
                latest_reader=lambda: latest,
                incoming=incoming,
                wait=lambda predicate: self.fail(
                    "sequence 12 was already consumed by the ACK wait"),
                observation_monitor=monitor)
            self.assertEqual(started, [])
            self.assertEqual(published, [])
            self.assertEqual(recovered["latest"]["sequence"], 12)
            self.assertEqual(recovered["submitted_sequence"], 11)
            self.assertEqual(recovered["invalidation"]["reason"],
                             "health:below_hard_minimum")
            self.assertEqual(monitor.seen, [12, 12])
            executor.submit("fresh-plan", [{"op": "observe"}],
                            recovered["latest"]["sequence"], deadline)

        self.assertEqual(started, ["fresh-plan"])
        self.assertEqual([event["id"] for event in published], ["fresh-plan"])

    def test_initial_stale_cover_fails_closed_when_no_new_full_observation_arrives(self):
        latest = {"sequence": 21}
        attempts = []
        rejected = {"event": "rejected", "id": "cover-21",
                    "reason": "latest observation sequence required before input"}

        def submit(_consumed_events):
            attempts.append(21)
            return rejected

        def wait(_predicate):
            raise TimeoutError("no newer full observation")

        with self.assertRaisesRegex(TimeoutError, "no newer full observation"):
            submit_initial_cover_with_recovery(
                submit, identifier="cover-21", latest_reader=lambda: latest,
                incoming=queue.Queue(), wait=wait,
                observation_monitor=Monitor())

        self.assertEqual(attempts, [21])
        self.assertEqual(latest["sequence"], 21)

    def test_drain_stops_at_fixed_budget_and_reports_remaining_backlog(self):
        incoming = queue.Queue()
        for sequence in range(1, MAX_PENDING_OBSERVATION_EVENTS + 3):
            incoming.put({"event": "observation", "sequence": sequence})
        monitor = Monitor()

        result = drain_pending_observation_events(incoming, monitor, "cover-4b")

        self.assertEqual(len(monitor.seen), MAX_PENDING_OBSERVATION_EVENTS)
        self.assertEqual(result["latest"]["sequence"], MAX_PENDING_OBSERVATION_EVENTS)
        self.assertTrue(result["pending_events"])
        self.assertEqual(incoming.qsize(), 2)

    def test_continuous_backlog_recovery_exhausts_a_finite_budget(self):
        class ReplenishingQueue(queue.Queue):
            def get_nowait(self):
                row = super().get_nowait()
                self.put({"event": "observation",
                          "sequence": row["sequence"] + 1})
                return row

        incoming = ReplenishingQueue()
        incoming.put({"event": "observation", "sequence": 1})

        result = settle_pending_observation_backlog(
            incoming, {"event": "observation", "sequence": 0}, "cover-flood")

        self.assertTrue(result["exhausted"])
        self.assertEqual(result["batches"], 4)
        self.assertEqual(incoming.qsize(), 1)
        self.assertEqual(result["latest"]["sequence"], 1024)

    def test_pending_backlog_is_discarded_before_waiting_for_fresh_source(self):
        source = Path(__file__).with_name("map01_overlap_controller_v39.py").read_text(
            encoding="utf-8")
        drain = source.index("drained = drain_pending_observation_events(")
        backlog_check = source.index('elif drained["pending_events"]:', drain)
        result = source.index("planner_result=future.result()", drain)
        discard = source.index("if invalidation is not None:", result)
        settle = source.index("recovery = recover_pending_observation_backlog(", discard)
        admission = source.index("final_action_admission=prepare_action_admission(", settle)
        helper = source.index("def recover_pending_observation_backlog(")
        settle_helper = source.index("settle_pending_observation_backlog(", helper)
        fresh_wait = source.index("row[\"sequence\"] > source_sequence", helper)
        self.assertLess(drain, backlog_check)
        self.assertLess(backlog_check, result)
        self.assertLess(result, discard)
        self.assertLess(discard, settle)
        self.assertLess(settle_helper, fresh_wait)
        self.assertLess(settle, admission)

    def test_production_paired_monitor_invalidates_queued_typed_health_crossing(self):
        binding = {"focus": 7, "surface": 9,
                   "geometry": [0, 0, 640, 480]}
        monitor = DoomCoverSignalPairMonitor(
            {"health": SignalGuard("health", 100, 10, 1_000_000_000, 80),
             "ammo": SignalGuard("ammo", 4, 10, 1_000_000_000, 1)},
            health_reader=None, ammo_reader=None)
        row = {
            "event": "typed_observation", "sequence": 11,
            "capture_ns": 1_100_000_000, "pointer_binding": binding,
            "frame_rgb_sha256": "a" * 64,
            "signals": {
                "health": typed_signal("health", 75, 11, 1_100_000_000,
                                        binding),
                "ammo": typed_signal("ammo", 4, 11, 1_100_000_000,
                                      binding),
            },
        }
        incoming = queue.Queue()
        incoming.put(row)

        result = drain_pending_observation_events(incoming, monitor, "cover-5")

        self.assertEqual(result["invalidation"]["event"],
                         "paired_signal_invalidation")
        self.assertEqual(result["invalidation"]["reason"],
                         "health:below_hard_minimum")
        self.assertTrue(incoming.empty())

    def test_production_monitor_preserves_cover_on_soft_typed_health_change(self):
        binding = {"focus": 7, "surface": 9,
                   "geometry": [0, 0, 640, 480]}
        monitor = DoomCoverSignalPairMonitor(
            {"health": SignalGuard("health", 100, 10, 1_000_000_000, 80),
             "ammo": SignalGuard("ammo", 4, 10, 1_000_000_000, 1)},
            health_reader=None, ammo_reader=None)
        incoming = queue.Queue()
        incoming.put({
            "event": "typed_observation", "sequence": 11,
            "capture_ns": 1_100_000_000, "pointer_binding": binding,
            "frame_rgb_sha256": "b" * 64,
            "signals": {
                "health": typed_signal("health", 95, 11, 1_100_000_000,
                                        binding),
                "ammo": typed_signal("ammo", 4, 11, 1_100_000_000,
                                      binding),
            },
        })

        result = drain_pending_observation_events(incoming, monitor, "cover-6")

        self.assertIsNone(result["invalidation"])
        self.assertIsNone(result["latest"])
        self.assertEqual(monitor.soft_event_count, 1)
        self.assertEqual(monitor.latest_soft_event["sequence"], 11)
        self.assertEqual(monitor.latest_soft_event["signal"]["value"], 95)


if __name__ == "__main__":
    unittest.main(verbosity=2)
