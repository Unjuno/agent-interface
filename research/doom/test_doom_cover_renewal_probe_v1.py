"""Exercise renewal witness policy without starting a display, model, or input owner."""
from copy import deepcopy
import threading
import time
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from PIL import Image

from doom_cover_renewal_probe_v1 import (
    PROBE_NS, PassiveProbeDelivery, capture_passive_probe, evaluate_passive_probe,
    probe_frame_path, request_passive_probe, settled_cover_probe_source, verify_probe_frame,
)
from observable_signal_guard_v2 import ObservableSignalGuard
from executor_v11 import program_sha256


STEPS = [{"op": "coast", "duration_ms": 5000, "sample_ms": 250}]
PROGRAM = program_sha256(STEPS)


def source():
    return {
        "sequence": 40, "capture_ns": 100, "input_owner_generation": 2, "renewal_owner_id": "owner",
        "previous_program_sha256": PROGRAM,
        "pointer_binding": {"focus": 7, "surface": 7, "geometry": [0, 0, 640, 480]},
        "target_process_identity": {"sequence": 40, "surface": 7, "digest": "a" * 64},
        "target_renewal_window_identity": {"sequence": 40, "surface": 7, "digest": "b" * 64},
    }


class Reader:
    def __init__(self, name, value):
        self.name, self.value = name, value

    def read_frame(self, row, _frame):
        return dict(format="observable-signal-v1", status="observed", signal_id=self.name,
                    value=self.value, sequence=row["sequence"], capture_ns=row["capture_ns"],
                    binding=deepcopy(row["pointer_binding"]), wad_sha256="c" * 64)


class RenewalProbeTests(unittest.TestCase):
    identifier = "cover-0-renew-1"
    previous = {"event": "terminal", "id": "cover-0", "terminal_ns": 110, "intent_token": "prior-intent",
                "program_sha256": PROGRAM}
    proof = {"pointer_binding": source()["pointer_binding"],
             "process_digest": "a" * 64, "window_digest": "b" * 64}

    def capture(self, health, proofs=None, output=None):
        original = source()
        proof_reader = Mock(side_effect=proofs or [self.proof, self.proof])
        sink = Mock(side_effect=lambda frame: frame.save(probe_frame_path(output, self.identifier))
                    if output is not None else None)
        times = iter(range(130, 150))
        row = capture_passive_probe(
            self.identifier, self.previous, original,
            read_proof=proof_reader, grab_frame=lambda: Image.new("RGB", (640, 480)),
            readers={"health": Reader("health", health), "ammo": Reader("ammo", 50)},
            publish_frame=sink, deadline=120 + PROBE_NS, clock=lambda: next(times))
        self.assertEqual(original, source())
        self.assertEqual(proof_reader.call_count, 2)
        sink.assert_called_once()
        return dict(row, approval_nonce="a" * 32)

    def guard(self):
        binding = source()["pointer_binding"]
        signal = {"status": "observed", "signal_id": "health", "value": 100,
                  "sequence": 40, "capture_ns": 100, "binding": binding}
        spec = dict(op="observable_signal_guard", guard_id="g", source_sequence=40,
                    signal_id="health", source_value=100, hard_minimum=98, max_source_age_ms=30000,
                    on_soft_change="preserve_existing_policy", on_hard_change="needs_decision",
                    on_unknown="needs_decision")
        return ObservableSignalGuard(spec, signal, binding)

    def evaluate(self, row):
        return evaluate_passive_probe(row, self.identifier, self.previous, source(),
                                      {"health": self.guard()}, started_ns=120, observed_ns=160)

    def test_passive_sample_has_no_authority_and_hard_value_vetoes(self):
        self.assertIsNone(self.evaluate(self.capture(100)))
        row = self.capture(97)
        self.assertFalse(row["grants_input_authority"])
        self.assertNotIn("sequence", row)
        self.assertEqual(row["source_sequence"], 40)
        invalidation = self.evaluate(row)
        self.assertEqual(invalidation["reason"], "health:below_hard_minimum")
        self.assertFalse(invalidation["grants_input_authority"])

    def test_continuity_and_staleness_fail_closed(self):
        for change in (
                {"capture_started_ns": 119}, {"id": "another-renewal"},
                {"previous_cover_id": "another-cover"}, {"source_sequence": 41},
                {"input_owner_generation": 3}, {"grants_input_authority": True},
                {"previous_intent_token": "other-intent"}, {"renewal_owner_id": "new-owner"},
                {"probe_sequence": 2}, {"deadline_ns": 120 + PROBE_NS + 1},
                {"target_renewal_window_identity": {"sequence": 40, "surface": 7, "digest": "d" * 64}}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.evaluate({**self.capture(100), **change})
        changed = {**self.proof, "window_digest": "d" * 64}
        with self.assertRaises(ValueError):
            self.capture(100, [self.proof, changed])

    def test_probe_dispatch_gate_stops_on_missing_reply_or_concurrent_completion(self):
        row = self.capture(100)
        probe = Mock(return_value=row)
        request = Mock()
        outcome = request_passive_probe(
            request, probe, self.identifier, self.previous, source(), {"health": self.guard()},
            done=lambda: True, verify_frame=lambda row: None, clock=Mock(side_effect=(120, 160)))
        self.assertFalse(outcome["admit_renewal"])
        request.assert_called_once_with({"op": "probe_cover_renewal", "id": self.identifier,
                                        "previous_cover_id": self.previous["id"], "expected_sequence": 40,
                                        "previous_intent_token": "prior-intent", "deadline_ns": 120 + PROBE_NS})
        with self.assertRaises(TimeoutError):
            request_passive_probe(request, Mock(side_effect=TimeoutError("missing proof")),
                                  self.identifier, self.previous, source(), {"health": self.guard()},
                                  done=lambda: False, verify_frame=lambda row: None, clock=lambda: 120)


    def test_retained_rgb_and_decoded_hud_are_both_required(self):
        readers = {"health": Reader("health", 97), "ammo": Reader("ammo", 50)}
        with TemporaryDirectory() as output:
            witness = self.capture(97, output=output)
            verify_probe_frame(output, witness, readers)
            tampered = deepcopy(witness)
            tampered["signals"]["health"]["value"] = 100
            with self.assertRaisesRegex(ValueError, "HUD differs"):
                verify_probe_frame(output, tampered, readers)
            tampered = {**witness, "frame_rgb_sha256": "d" * 64}
            with self.assertRaisesRegex(ValueError, "frame digest"):
                verify_probe_frame(output, tampered, readers)

    def test_blocked_worker_allows_immediate_cancellation_and_cannot_emit_late_proof(self):
        entered = threading.Event()
        unblocked = threading.Event()
        output = Mock()
        original = source()

        def capture(identifier, previous, copied, deadline, cancelled):
            entered.set()
            if not unblocked.wait(2):
                raise TimeoutError("test capture not released")
            self.assertTrue(cancelled())
            return {"event": "cover_renewal_passive_observation"}

        delivery = PassiveProbeDelivery(lambda command: deepcopy(original), capture, output)
        delivery.start({"op": "probe_cover_renewal", "id": self.identifier,
                        "previous_cover_id": self.previous["id"], "previous_intent_token": "prior-intent",
                        "expected_sequence": 40, "deadline_ns": time.perf_counter_ns() + PROBE_NS})
        try:
            self.assertTrue(entered.wait(1))
            delivery.cancel()
            self.assertTrue(delivery.worker.is_alive())
            output.assert_not_called()
        finally:
            unblocked.set()
            delivery.worker.join(1)
        self.assertFalse(delivery.worker.is_alive())
        self.assertEqual(original, source())
        output.assert_not_called()


    def test_one_shot_admission_refuses_replay_expiry_and_owner_change(self):
        for case in ("good", "expired", "changed", "other-id", "bad-nonce", "changed-steps"):
            with self.subTest(case=case):
                current = source()
                rows = []
                delivery = PassiveProbeDelivery(
                    lambda command: deepcopy(current),
                    lambda *_: {"event": "cover_renewal_passive_observation"},
                    rows.append)
                deadline = time.perf_counter_ns() + PROBE_NS
                command = {"op": "probe_cover_renewal", "id": self.identifier,
                           "previous_cover_id": self.previous["id"], "previous_intent_token": "prior-intent",
                           "expected_sequence": 40, "deadline_ns": deadline}
                delivery.start(command)
                delivery.worker.join(1)
                self.assertEqual(len(rows), 1)
                request = {"id": self.identifier, "renewal_approval": rows[0]["approval_nonce"],
                           "expected_sequence": 40, "steps": deepcopy(STEPS)}
                if case == "good":
                    self.assertEqual(delivery.consume(request), deadline)
                elif case == "changed":
                    current["renewal_owner_id"] = "replacement"
                elif case == "other-id":
                    request["id"] = "cover-0-renew-2"
                elif case == "bad-nonce":
                    request["renewal_approval"] = "c" * 32
                elif case == "changed-steps":
                    request["steps"][0]["duration_ms"] = 2000
                if case == "expired":
                    from unittest.mock import patch
                    with patch("doom_cover_renewal_probe_v1.time.perf_counter_ns", return_value=deadline):
                        with self.assertRaisesRegex(ValueError, "stale"):
                            delivery.consume(request)
                else:
                    with self.assertRaisesRegex(ValueError, "stale"):
                        delivery.consume(request)


    def test_source_gate_refuses_an_executor_lock_held_by_another_thread(self):
        lock = threading.RLock()
        entered, release = threading.Event(), threading.Event()
        executor = SimpleNamespace(lock=lock, active=None, closed=False)
        backend = SimpleNamespace(cover_renewal_source=Mock(return_value=source()))
        command = {"previous_cover_id": "cover-0", "previous_intent_token": "prior-intent",
                   "expected_sequence": 40}
        previous = {**self.previous, "status": "completed", "input_owner_generation": 2,
                    "input_owner_id": "owner",
                    "release": {"verified": True, "keys_down": [], "buttons_down": [],
                                "keys_unknown": [], "key_state_errors": []}}
        accepted = {"id": "cover-0", "intent_token": "prior-intent", "program_sha256": PROGRAM}

        def hold():
            with lock:
                entered.set()
                release.wait(2)

        worker = threading.Thread(target=hold)
        worker.start()
        try:
            self.assertTrue(entered.wait(1))
            with self.assertRaisesRegex(ValueError, "executor unavailable"):
                settled_cover_probe_source(executor, backend, previous, accepted, command)
            backend.cover_renewal_source.assert_not_called()
            self.assertTrue(worker.is_alive())
        finally:
            release.set()
            worker.join(1)
        self.assertEqual(settled_cover_probe_source(executor, backend, previous, accepted, command),
                         source())
        for changed in (
            {**previous, "release": {**previous["release"], "intent_token": "other-intent"}},
            {**previous, "input_owner_id": "another-owner"},
            {**previous, "input_owner_generation": 3},
        ):
            with self.assertRaises(ValueError):
                settled_cover_probe_source(executor, backend, changed, accepted, command)

if __name__ == "__main__":
    unittest.main()
