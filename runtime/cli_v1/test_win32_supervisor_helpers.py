import unittest
import os
from tempfile import TemporaryDirectory
from unittest.mock import patch

from runtime.cli_v1.win32_supervisor_helpers import (
    _helper_main, _observe, _parse_obligations, _recover)
from runtime.cli_v1 import win32_supervisor_helpers as supervisor_helpers
from runtime.guarded_win32_v1.process_cancellation import (
    OperationCancellationSupervisor, _consistent_neutral_observation)


GENERATION = "a" * 64
OPERATION = "1" * 32


class FakeBackend:
    def __init__(self, targets, generation=GENERATION, states=None,
                 release_verified=True):
        self.targets = targets
        self.generation = generation
        self.states = dict(states or {})
        self.release_verified = release_verified
        self.held_keys = {}
        self.held_key_encodings = {}
        self.held_key_targets = {}
        self.held_buttons = set()
        self.held_button_targets = {}
        self.pending_unicode_ups = set()
        self.release_calls = 0
        self.release_snapshot = None
        self.closed = False
        self.events = []
        self.key_up_calls = []

    def target_generation(self, target):
        if target not in self.targets:
            raise RuntimeError("unknown target")
        return self.generation

    def release_all(self):
        self.events.append("release")
        self.release_calls += 1
        for key, vk in list(self.held_keys.items()):
            encoding = self.held_key_encodings.get(key)
            self._send_key(vk, False, encoding)
        self.release_snapshot = (dict(self.held_keys),
                                 dict(self.held_key_encodings), set(self.held_buttons),
                                 set(self.pending_unicode_ups))
        self.held_keys.clear()
        self.held_key_encodings.clear()
        self.held_key_targets.clear()
        self.held_buttons.clear()
        self.held_button_targets.clear()
        self.pending_unicode_ups.clear()
        return {"verified": self.release_verified,
                "keys_down": [], "buttons_down": [],
                "keys_unknown": [], "buttons_unknown": []}

    def focus(self, target):
        self.events.append(("focus", target))

    def _key_down_state(self, vk, target):
        return self.states.get((vk, target), False)

    def _send_key(self, vk, down, encoding=None):
        self.key_up_calls.append((vk, down, encoding))

    def close(self):
        self.closed = True


class NativeWin32SupervisorHelperTests(unittest.TestCase):
    def request(self, **changes):
        request = {"operation_id": "1" * 32,
            "target_generation": GENERATION, "recovery_id": "2" * 32,
            "request_id": "2" * 32, "deadline_ns": 100,
            "obligations": ["key:fixture:CTRL", "button:fixture:left",
                            "unicode:0041"]}
        request.update(changes)
        return request

    def test_supervisor_retains_key_up_encoding_before_readback(self):
        class Owner:
            def __init__(self):
                self.attempts = None
                self.completed = []
                self.unknown = []
            def recovery_release_attempted(self, _op, _gen, _recovery_id,
                                           attempts):
                self.attempts = attempts
            def recovery_completed(self, *args, **kwargs):
                self.completed.append((args, kwargs))
                return True
            def mark_unknown(self, _op, _gen, reason):
                self.unknown.append(reason)

        owner = Owner()
        supervisor = object.__new__(OperationCancellationSupervisor)
        supervisor._owner = owner
        supervisor._clock_ns = lambda: 10
        supervisor.late_input_horizon_ns = 0
        supervisor._invalidate_helper = lambda *_: None
        recovery_id = "3" * 32
        attempts = [{"virtual_key": 0x57, "encoding": "scan_code",
                     "status": "returned"}]
        def exchange(role, request, _deadline):
            if role == "recovery":
                return {"operation_id": OPERATION,
                    "target_generation": GENERATION,
                    "recovery_id": recovery_id, "release_accepted": True,
                    "release_key_up_attempts": attempts}
            return {"operation_id": OPERATION,
                "target_generation": GENERATION,
                "recovery_id": recovery_id, "neutral": True,
                "observed_monotonic_ns": 10,
                "key_button_states": [False], "unicode_event_units": 0}
        supervisor._exchange_helper = exchange
        request = {"operation_id": OPERATION,
            "target_generation": GENERATION, "recovery_id": recovery_id,
            "deadline_ns": 100, "obligations": ["key:fixture:W"]}
        supervisor._run_recovery(OPERATION, GENERATION, request)
        self.assertEqual(owner.attempts, attempts)
        self.assertEqual(len(owner.completed), 1)
        self.assertEqual(owner.unknown, [])

    def test_parse_obligations_retains_each_input_domain(self):
        result = _parse_obligations(self.request()["obligations"])
        self.assertEqual(result, {"keys": [("fixture", "CTRL", "virtual_key")],
            "buttons": [("fixture", "left")], "unicode": [0x41]})

    def test_parse_obligations_preserves_colons_in_configured_target_names(self):
        result = _parse_obligations([
            "key:desk:game:W:scan_code",
            "button:desk:game:left",
        ])
        self.assertEqual(result, {
            "keys": [("desk:game", "W", "scan_code")],
            "buttons": [("desk:game", "left")],
            "unicode": [],
        })

    def test_orphan_recovery_releases_key_for_colon_target_name(self):
        backend = FakeBackend({"desk:game": 44})
        result = _recover(self.request(obligations=[
                "key:desk:game:W:scan_code"]),
            backend_factory=lambda _targets: backend, clock_ns=lambda: 10,
            configured_targets={"desk:game": 44})
        self.assertTrue(result["release_accepted"])
        self.assertEqual(backend.targets, {"desk:game": 44})
        self.assertEqual(backend.release_snapshot[1], {"W": "scan_code"})
        self.assertEqual(result["release_key_up_attempts"], [{
            "virtual_key": 0x57, "encoding": "scan_code",
            "status": "returned"}])

    def test_cancel_recovery_rejects_stale_or_invalid_readback_time(self):
        for observed in (9, 11, None, True):
            with self.subTest(observed=observed):
                class Owner:
                    def __init__(self): self.unknown = []; self.completed = []; self.attempts = []
                    def mark_unknown(self, operation_id, generation, reason): self.unknown.append(reason)
                    def recovery_release_attempted(self, *args): self.attempts.append(args)
                    def recovery_completed(self, *args, **kwargs): self.completed.append((args, kwargs))
                owner = Owner()
                supervisor = object.__new__(OperationCancellationSupervisor)
                supervisor._owner = owner
                supervisor._clock_ns = lambda: 10
                supervisor._invalidate_helper = lambda *_: None
                recovery_id = "3" * 32
                def exchange(role, request, deadline):
                    row = {"operation_id": OPERATION, "target_generation": GENERATION,
                           "recovery_id": recovery_id}
                    if role == "recovery":
                        row["release_accepted"] = True
                        row["release_key_up_attempts"] = []
                    else: row.update(neutral=True, observed_monotonic_ns=observed,
                        key_button_states=[False for item in request["obligations"] if item.startswith(("key:", "button:"))],
                        unicode_event_units=sum(item.startswith("unicode:") for item in request["obligations"]))
                    return row
                supervisor._exchange_helper = exchange
                supervisor._run_recovery(OPERATION, GENERATION,
                    {"operation_id": OPERATION, "target_generation": GENERATION,
                     "recovery_id": recovery_id, "deadline_ns": 100, "obligations": []})
                self.assertEqual(owner.completed, [])
                self.assertEqual(owner.unknown, ["independent_readback_time_invalid"])

    def test_cancel_recovery_rejects_contradictory_neutral_state(self):
        class Owner:
            def __init__(self): self.unknown = []; self.completed = []; self.attempts = []
            def mark_unknown(self, op, generation, reason): self.unknown.append(reason)
            def recovery_release_attempted(self, *args): self.attempts.append(args)
            def recovery_completed(self, *args, **kwargs): self.completed.append((args, kwargs))
        owner = Owner()
        supervisor = object.__new__(OperationCancellationSupervisor)
        supervisor._owner = owner; supervisor._clock_ns = lambda: 10
        supervisor._invalidate_helper = lambda *_: None
        recovery_id = "3" * 32
        def exchange(role, request, deadline):
            row = {"operation_id": OPERATION, "target_generation": GENERATION,
                   "recovery_id": recovery_id}
            if role == "recovery":
                row["release_accepted"] = True
                row["release_key_up_attempts"] = []
            else: row.update(neutral=True, observed_monotonic_ns=10,
                key_button_states=[True], unicode_event_units=0)
            return row
        supervisor._exchange_helper = exchange
        supervisor._run_recovery(OPERATION, GENERATION,
            {"operation_id": OPERATION, "target_generation": GENERATION,
             "recovery_id": recovery_id, "deadline_ns": 100,
             "obligations": ["key:fixture:W"]})
        self.assertEqual(owner.completed, [])
        self.assertEqual(owner.unknown, ["independent_readback_state_invalid"])

    def test_orphan_recovery_requires_matching_release_and_independent_readback(self):
        supervisor = object.__new__(OperationCancellationSupervisor)
        supervisor._clock_ns = lambda: 10
        recovery_id = "3" * 32
        requests = []
        def exchange(role, request, deadline):
            requests.append((role, request, deadline))
            row = {"operation_id": OPERATION,
                "source_target_generation": request.get(
                    "source_target_generation", GENERATION),
                "target_generation": GENERATION,
                "recovery_id": recovery_id}
            if role == "recovery":
                row["release_accepted"] = True
            else:
                row["neutral"] = True
                row["observed_monotonic_ns"] = 10
                row["key_button_states"] = [False for item in request["obligations"] if item.startswith(("key:", "button:"))]
                row["unicode_event_units"] = sum(item.startswith("unicode:") for item in request["obligations"])
            return row
        supervisor._exchange_helper = exchange
        supervisor._invalidate_helper = lambda *_: self.fail(
            "valid exact recovery must not retire a helper")

        result = supervisor.recover_orphaned_input(OPERATION, GENERATION,
            recovery_id, 100, ["key:fixture:W"])

        self.assertEqual(result["status"], "recovered")
        self.assertTrue(result["release_confirmed"])
        self.assertEqual(result["operation_id"], OPERATION)
        self.assertEqual(result["target_generation"], GENERATION)
        self.assertEqual(result["recovery_id"], recovery_id)
        self.assertEqual([row[0] for row in requests], ["recovery", "observer"])
        self.assertEqual(requests[0][1]["obligations"], ["key:fixture:W"])
        self.assertEqual(requests[0][1]["request_id"], recovery_id)
        self.assertTrue(requests[0][1]["focus_target_before_release"])
        self.assertEqual(requests[1][1]["request_id"], recovery_id)

    def test_orphan_recovery_uses_validated_obligation_snapshot(self):
        supervisor = object.__new__(OperationCancellationSupervisor)
        obligations = ["key:fixture:W"]
        calls = []
        def clock():
            obligations[:] = ["key:fixture:CTRL"]
            return 10
        supervisor._clock_ns = clock
        recovery_id = "3" * 32
        def exchange(role, request, deadline):
            calls.append((role, list(request["obligations"])))
            row = {"operation_id": OPERATION,
                   "source_target_generation": request.get(
                       "source_target_generation", GENERATION),
                   "target_generation": GENERATION,
                   "recovery_id": recovery_id}
            row["release_accepted" if role == "recovery" else "neutral"] = True
            if role == "observer":
                row["observed_monotonic_ns"] = 10
                row["key_button_states"] = [False for item in request["obligations"] if item.startswith(("key:", "button:"))]
                row["unicode_event_units"] = sum(item.startswith("unicode:") for item in request["obligations"])
            return row
        supervisor._exchange_helper = exchange
        supervisor._invalidate_helper = lambda *_: self.fail("unexpected invalidation")
        result = supervisor.recover_orphaned_input(OPERATION, GENERATION,
            recovery_id, 100, obligations)
        self.assertEqual(result["status"], "recovered")
        self.assertEqual(calls, [("recovery", ["key:fixture:W"]),
                                 ("observer", ["key:fixture:W"])])
        self.assertEqual(obligations, ["key:fixture:CTRL"])

    def test_orphan_recovery_binds_release_to_new_generation_and_keeps_source(self):
        supervisor = object.__new__(OperationCancellationSupervisor)
        supervisor._clock_ns = lambda: 10
        recovery_id = "4" * 32
        recovery_generation = "b" * 64
        requests = []

        def exchange(role, request, deadline):
            requests.append((role, dict(request)))
            row = {"operation_id": OPERATION,
                "source_target_generation": request[
                    "source_target_generation"],
                "target_generation": request["target_generation"],
                "recovery_id": recovery_id}
            if role == "recovery":
                row["release_accepted"] = True
            else:
                row.update(neutral=True, observed_monotonic_ns=10,
                    key_button_states=[False], unicode_event_units=0)
            return row

        supervisor._exchange_helper = exchange
        supervisor._invalidate_helper = lambda *_: self.fail(
            "valid new-generation recovery must preserve helpers")
        result = supervisor.recover_orphaned_input(OPERATION, GENERATION,
            recovery_id, 100, ["key:fixture:W"],
            recovery_target_generation=recovery_generation)

        self.assertEqual(result["status"], "recovered")
        self.assertEqual(result["target_generation"], GENERATION)
        self.assertEqual(result["source_target_generation"], GENERATION)
        self.assertEqual(result["recovery_target_generation"],
                         recovery_generation)
        self.assertEqual(requests[0][1]["source_target_generation"], GENERATION)
        self.assertEqual(requests[0][1]["target_generation"],
                         recovery_generation)
        self.assertEqual(requests[1][1]["target_generation"],
                         recovery_generation)

    def test_orphan_recovery_retains_bound_late_input_horizon(self):
        supervisor = object.__new__(OperationCancellationSupervisor)
        now = [10]
        supervisor._clock_ns = lambda: now[0]
        supervisor.late_input_horizon_ns = 20
        supervisor._late_input_sample_interval_s = 0.00000001
        recovery_id = "3" * 32
        requests = []
        def exchange(role, request, deadline):
            requests.append(role)
            row = {"operation_id": OPERATION,
                "source_target_generation": request.get(
                    "source_target_generation", GENERATION),
                "target_generation": GENERATION, "recovery_id": recovery_id}
            if role == "recovery":
                row["release_accepted"] = True
            else:
                row.update(neutral=True, observed_monotonic_ns=now[0],
                    key_button_states=[False], unicode_event_units=0)
            return row
        supervisor._exchange_helper = exchange
        supervisor._invalidate_helper = lambda *_: self.fail(
            "valid horizon observations must preserve the helpers")
        def advance(_seconds):
            now[0] += 10

        with patch("runtime.guarded_win32_v1.process_cancellation.time.sleep",
                   side_effect=advance):
            result = supervisor.recover_orphaned_input(OPERATION, GENERATION,
                recovery_id, 100, ["key:fixture:W"])

        self.assertEqual(result["status"], "recovered")
        self.assertTrue(result["release_confirmed"])
        self.assertTrue(result["late_input_horizon_verified"])
        self.assertEqual(result["late_input_horizon_ns"], 20)
        self.assertEqual(result["late_input_observation_count"], 3)
        self.assertEqual(result["late_input_release_received_monotonic_ns"], 10)
        self.assertEqual(result["late_input_observation_end_monotonic_ns"], 30)
        self.assertEqual(requests, ["recovery", "observer", "observer", "observer"])

    def test_orphan_recovery_keeps_release_unknown_on_delayed_input_in_horizon(self):
        supervisor = object.__new__(OperationCancellationSupervisor)
        now = [10]
        supervisor._clock_ns = lambda: now[0]
        supervisor.late_input_horizon_ns = 20
        supervisor._late_input_sample_interval_s = 0.00000001
        recovery_id = "3" * 32
        observer_count = [0]
        def exchange(role, request, deadline):
            row = {"operation_id": OPERATION,
                "source_target_generation": request.get(
                    "source_target_generation", GENERATION),
                "target_generation": GENERATION, "recovery_id": recovery_id}
            if role == "recovery":
                row["release_accepted"] = True
            else:
                observer_count[0] += 1
                delayed_down = observer_count[0] == 2
                row.update(neutral=not delayed_down,
                    observed_monotonic_ns=now[0],
                    key_button_states=[delayed_down], unicode_event_units=0)
            return row
        supervisor._exchange_helper = exchange
        supervisor._invalidate_helper = lambda *_: None
        def advance(_seconds):
            now[0] += 10

        with patch("runtime.guarded_win32_v1.process_cancellation.time.sleep",
                   side_effect=advance):
            result = supervisor.recover_orphaned_input(OPERATION, GENERATION,
                recovery_id, 100, ["key:fixture:W"])

        self.assertEqual(result["status"], "unknown")
        self.assertFalse(result["release_confirmed"])
        self.assertEqual(result["reason"], "late_input_horizon_unconfirmed")

    def test_orphan_recovery_reports_the_deadline_checked_completion_time(self):
        supervisor = object.__new__(OperationCancellationSupervisor)
        times = iter((10, 10, 99, 100))
        supervisor._clock_ns = lambda: next(times)
        recovery_id = "3" * 32
        def exchange(role, request, deadline):
            row = {"operation_id": OPERATION,
                   "source_target_generation": request.get(
                       "source_target_generation", GENERATION),
                   "target_generation": GENERATION,
                   "recovery_id": recovery_id}
            row["release_accepted" if role == "recovery" else "neutral"] = True
            if role == "observer":
                row["observed_monotonic_ns"] = 10
                row["key_button_states"] = [False for item in request["obligations"] if item.startswith(("key:", "button:"))]
                row["unicode_event_units"] = sum(item.startswith("unicode:") for item in request["obligations"])
            return row
        supervisor._exchange_helper = exchange
        supervisor._invalidate_helper = lambda *_: self.fail("unexpected invalidation")
        result = supervisor.recover_orphaned_input(OPERATION, GENERATION,
            recovery_id, 100, ["key:fixture:W"])
        self.assertEqual(result["status"], "recovered")
        self.assertEqual(result["recovery_completed_monotonic_ns"], 99)

    def test_orphan_neutral_readback_at_deadline_is_not_recovered(self):
        supervisor = object.__new__(OperationCancellationSupervisor)
        times = iter((10, 10, 100))
        supervisor._clock_ns = lambda: next(times)
        recovery_id = "3" * 32
        def exchange(role, request, deadline):
            row = {"operation_id": OPERATION, "target_generation": GENERATION,
                   "recovery_id": recovery_id}
            row["release_accepted" if role == "recovery" else "neutral"] = True
            if role == "observer":
                row["observed_monotonic_ns"] = 10
                row["key_button_states"] = [False for item in request["obligations"] if item.startswith(("key:", "button:"))]
                row["unicode_event_units"] = sum(item.startswith("unicode:") for item in request["obligations"])
            return row
        supervisor._exchange_helper = exchange
        invalidated = []
        supervisor._invalidate_helper = lambda role, deadline: invalidated.append(role)
        result = supervisor.recover_orphaned_input(OPERATION, GENERATION,
            recovery_id, 100, ["key:fixture:W"])
        self.assertEqual(result["status"], "unknown")
        self.assertFalse(result["release_confirmed"])
        self.assertEqual(invalidated, ["observer"])

    def test_orphan_recovery_rejects_pre_release_or_invalid_readback_time(self):
        for observed in (9, 101, None, True):
            with self.subTest(observed=observed):
                supervisor = object.__new__(OperationCancellationSupervisor)
                supervisor._clock_ns = lambda: 10
                recovery_id = "3" * 32
                def exchange(role, request, deadline):
                    row = {"operation_id": OPERATION, "target_generation": GENERATION,
                           "recovery_id": recovery_id}
                    if role == "recovery": row["release_accepted"] = True
                    else: row.update(neutral=True, observed_monotonic_ns=observed,
                        key_button_states=[False for item in request["obligations"] if item.startswith(("key:", "button:"))],
                        unicode_event_units=sum(item.startswith("unicode:") for item in request["obligations"]))
                    return row
                supervisor._exchange_helper = exchange
                supervisor._invalidate_helper = lambda *_: None
                result = supervisor.recover_orphaned_input(OPERATION, GENERATION,
                    recovery_id, 100, ["key:fixture:W"])
                self.assertEqual(result["status"], "unknown")
                self.assertFalse(result["release_confirmed"])

    def test_observer_state_coverage_includes_unicode_units(self):
        obligations = ["key:fixture:W", "button:fixture:left", "unicode:0041"]
        row = {"neutral": True, "key_button_states": [False, False],
               "unicode_event_units": 1}
        self.assertTrue(_consistent_neutral_observation(row, obligations))
        self.assertFalse(_consistent_neutral_observation(
            dict(row, unicode_event_units=0), obligations))
        self.assertTrue(_consistent_neutral_observation(
            {"neutral": False, "key_button_states": [None, False],
             "unicode_event_units": 1}, obligations))

    def test_orphan_recovery_rejects_inconsistent_observer_states(self):
        for states, unicode_units in (([True], 0), ([], 0), ([0], 0),
                                      ([False], 1), (None, 0)):
            with self.subTest(states=states, unicode_units=unicode_units):
                supervisor = object.__new__(OperationCancellationSupervisor)
                supervisor._clock_ns = lambda: 10
                recovery_id = "3" * 32
                def exchange(role, request, deadline):
                    row = {"operation_id": OPERATION, "target_generation": GENERATION,
                           "recovery_id": recovery_id}
                    if role == "recovery": row["release_accepted"] = True
                    else: row.update(neutral=True, observed_monotonic_ns=10,
                        key_button_states=states, unicode_event_units=unicode_units)
                    return row
                supervisor._exchange_helper = exchange
                supervisor._invalidate_helper = lambda *_: None
                result = supervisor.recover_orphaned_input(OPERATION, GENERATION,
                    recovery_id, 100, ["key:fixture:W"])
                self.assertEqual(result["status"], "unknown")
                self.assertFalse(result["release_confirmed"])

    def test_orphan_recovery_does_not_claim_release_without_neutral_observer(self):
        supervisor = object.__new__(OperationCancellationSupervisor)
        supervisor._clock_ns = lambda: 10
        recovery_id = "3" * 32
        roles = []
        def exchange(role, request, deadline):
            roles.append(role)
            row = {"operation_id": OPERATION,
                "target_generation": GENERATION,
                "recovery_id": recovery_id}
            if role == "recovery":
                row["release_accepted"] = True
            else:
                row["neutral"] = False
                row["observed_monotonic_ns"] = 10
                row["key_button_states"] = [True]
                row["unicode_event_units"] = 0
            return row
        supervisor._exchange_helper = exchange
        supervisor._invalidate_helper = lambda *_: None

        result = supervisor.recover_orphaned_input(OPERATION, GENERATION,
            recovery_id, 100, ["key:fixture:W"])

        self.assertEqual(result["status"], "unknown")
        self.assertFalse(result["release_confirmed"])
        self.assertEqual(roles, ["recovery", "observer"])

    def test_recovery_releases_only_frozen_obligations_after_generation_check(self):
        instances = []
        def factory(targets):
            backend = FakeBackend(targets)
            instances.append(backend)
            return backend
        result = _recover(self.request(), backend_factory=factory,
                          clock_ns=lambda: 10,
                          configured_targets={"fixture": 44})
        self.assertIs(result["release_accepted"], True)
        self.assertEqual(result["operation_id"], "1" * 32)
        self.assertEqual(instances[0].release_snapshot,
            ({"CTRL": 0x11}, {"CTRL": "virtual_key"}, {"left"}, {0x41}))

    def test_orphan_recovery_restores_original_scan_code_encoding(self):
        backend = FakeBackend({"fixture": 44})
        result = _recover(self.request(obligations=[
                "key:fixture:W:scan_code"]),
            backend_factory=lambda _targets: backend, clock_ns=lambda: 10,
            configured_targets={"fixture": 44})
        self.assertTrue(result["release_accepted"])
        self.assertEqual(backend.release_snapshot[0], {"W": 0x57})
        self.assertEqual(backend.release_snapshot[1], {"W": "scan_code"})
        self.assertEqual(result["release_key_up_attempts"], [{
            "virtual_key": 0x57, "encoding": "scan_code",
            "status": "returned"}])

    def test_post_release_deadline_keeps_release_and_up_attempt_receipts(self):
        backend = FakeBackend({"fixture": 44})
        clock_values = iter((10, 10, 100))
        result = _recover(self.request(obligations=[
                "key:fixture:W:scan_code"]),
            backend_factory=lambda _targets: backend,
            clock_ns=lambda: next(clock_values),
            configured_targets={"fixture": 44})

        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["reason"], "deadline_expired_after_release")
        self.assertEqual(result["error_type"], "TimeoutError")
        self.assertFalse(result["release_accepted"])
        self.assertEqual(result["release_receipt"], {
            "verified": True, "keys_down": [], "buttons_down": [],
            "keys_unknown": [], "buttons_unknown": []})
        self.assertEqual(result["release_key_up_attempts"], [{
            "virtual_key": 0x57, "encoding": "scan_code",
            "status": "returned"}])
        self.assertEqual(backend.release_calls, 1)

    def test_helper_main_transmits_post_release_unknown_receipt_without_loss(self):
        class Connection:
            def __init__(self, request):
                self.incoming = iter((request, None))
                self.sent = []
            def send(self, value):
                self.sent.append(value)
            def recv(self):
                return next(self.incoming)

        backend = FakeBackend({"fixture": 44})
        request = self.request(obligations=["key:fixture:W:scan_code"])
        connection = Connection(request)
        clock_values = iter((10, 10, 100))
        original_recover = supervisor_helpers._recover

        def recover_with_inert_backend(row, *, configured_targets):
            return original_recover(row,
                backend_factory=lambda _targets: backend,
                clock_ns=lambda: next(clock_values),
                configured_targets=configured_targets)

        with patch.object(supervisor_helpers, "_recover",
                          side_effect=recover_with_inert_backend):
            _helper_main("recovery", {"fixture": 44}, connection)

        self.assertEqual(connection.sent[0], {
            "status": "ready", "helper": "recovery"})
        response = connection.sent[1]
        self.assertEqual(response["status"], "unknown")
        self.assertEqual(response["reason"], "deadline_expired_after_release")
        self.assertEqual(response["operation_id"], request["operation_id"])
        self.assertFalse(response["release_accepted"])
        self.assertIsInstance(response["release_receipt"], dict)
        self.assertEqual(response["release_key_up_attempts"], [{
            "virtual_key": 0x57, "encoding": "scan_code",
            "status": "returned"}])

    def test_orphan_recovery_releases_each_encoding_for_one_logical_key(self):
        backend = FakeBackend({"fixture": 44})
        sent = []
        backend._send_key = lambda vk, down, encoding=None: sent.append(
            (vk, down, encoding))
        result = _recover(self.request(obligations=[
                "key:fixture:W:scan_code", "key:fixture:W:virtual_key"]),
            backend_factory=lambda _targets: backend, clock_ns=lambda: 10,
            configured_targets={"fixture": 44})
        self.assertTrue(result["release_accepted"])
        self.assertEqual(sent, [(0x57, False, "scan_code"),
                                (0x57, False, "virtual_key")])
        self.assertEqual(result["release_key_up_attempts"], [
            {"virtual_key": 0x57, "encoding": "scan_code",
             "status": "returned"},
            {"virtual_key": 0x57, "encoding": "virtual_key",
             "status": "returned"}])
        self.assertEqual(backend.release_snapshot[1], {"W": "virtual_key"})

    def test_orphan_recovery_preserves_failed_key_up_attempt(self):
        backend = FakeBackend({"fixture": 44})
        def fail_send(_vk, down, _encoding=None):
            if down is False:
                raise OSError("injected failure")
        backend._send_key = fail_send
        result = _recover(self.request(obligations=[
                "key:fixture:W:scan_code"]),
            backend_factory=lambda _targets: backend, clock_ns=lambda: 10,
            configured_targets={"fixture": 44})
        self.assertFalse(result["release_accepted"])
        self.assertEqual(result["release_error_type"], "OSError")
        self.assertEqual(result["release_key_up_attempts"], [{
            "virtual_key": 0x57, "encoding": "scan_code",
            "status": "raised", "error_type": "OSError"}])

    def test_orphan_recovery_continues_after_one_encoding_up_raises(self):
        backend = FakeBackend({"fixture": 44})
        sent = []
        def fail_scan_code(vk, down, encoding=None):
            sent.append((vk, down, encoding))
            if down is False and encoding == "scan_code":
                raise OSError("scan-code UP rejected")
        backend._send_key = fail_scan_code
        result = _recover(self.request(obligations=[
                "key:fixture:W:scan_code", "key:fixture:W:virtual_key"]),
            backend_factory=lambda _targets: backend, clock_ns=lambda: 10,
            configured_targets={"fixture": 44})
        self.assertTrue(result["release_accepted"])
        self.assertEqual(sent, [(0x57, False, "scan_code"),
                                (0x57, False, "virtual_key")])
        self.assertEqual(result["release_key_up_attempts"], [
            {"virtual_key": 0x57, "encoding": "scan_code",
             "status": "raised", "error_type": "OSError"},
            {"virtual_key": 0x57, "encoding": "virtual_key",
             "status": "returned"}])
        self.assertEqual(backend.release_snapshot[1], {"W": "virtual_key"})

    def test_orphan_release_helper_checks_new_target_generation(self):
        recovery_generation = "b" * 64
        backend = FakeBackend({"fixture": 44}, generation=recovery_generation)
        request = self.request(obligations=["key:fixture:W"],
            source_target_generation=GENERATION,
            target_generation=recovery_generation,
            focus_target_before_release=True)
        result = _recover(request, backend_factory=lambda _targets: backend,
            clock_ns=lambda: 10, configured_targets={"fixture": 44})
        self.assertTrue(result["release_accepted"])
        self.assertEqual(result["source_target_generation"], GENERATION)
        self.assertEqual(result["target_generation"], recovery_generation)
        self.assertEqual(backend.events, [("focus", "fixture"), "release"])
        self.assertTrue(backend.closed)

    def test_recovery_rejects_contradictory_or_incomplete_release_receipts(self):
        for field, value in (("keys_down", ["CTRL"]), ("buttons_down", ["left"]),
                             ("keys_unknown", ["CTRL"]), ("buttons_unknown", ["left"]),
                             ("keys_unknown", None), ("buttons_unknown", None)):
            with self.subTest(field=field, value=value):
                class ContradictoryBackend(FakeBackend):
                    def release_all(self):
                        receipt = super().release_all()
                        receipt[field] = value
                        return receipt
                result = _recover(self.request(),
                    backend_factory=lambda targets: ContradictoryBackend(targets),
                    clock_ns=lambda: 10, configured_targets={"fixture": 44})
                self.assertFalse(result["release_accepted"])

    def test_contradictory_native_release_stops_supervisor_before_readback(self):
        class Owner:
            def __init__(self): self.unknown = []; self.completed = []; self.attempts = []
            def mark_unknown(self, op, generation, reason): self.unknown.append(reason)
            def recovery_release_attempted(self, *args): self.attempts.append(args)
            def recovery_completed(self, *args, **kwargs): self.completed.append((args, kwargs))
        class ContradictoryBackend(FakeBackend):
            def release_all(self):
                receipt = super().release_all()
                receipt["keys_unknown"] = ["CTRL"]
                return receipt
        owner = Owner()
        supervisor = object.__new__(OperationCancellationSupervisor)
        supervisor._owner = owner; supervisor._clock_ns = lambda: 10
        invalidated = []; supervisor._invalidate_helper = lambda role, deadline: invalidated.append(role)
        roles = []
        def exchange(role, request, deadline):
            roles.append(role)
            if role != "recovery": self.fail("observer must not run after invalid release")
            return _recover(request,
                backend_factory=lambda targets: ContradictoryBackend(targets),
                clock_ns=lambda: 10, configured_targets={"fixture": 44})
        supervisor._exchange_helper = exchange
        request = self.request()
        supervisor._run_recovery(request["operation_id"], request["target_generation"], request)
        self.assertEqual(roles, ["recovery"])
        self.assertEqual(owner.completed, [])
        self.assertEqual(owner.unknown, ["recovery_receipt_invalid_or_late"])
        self.assertEqual(invalidated, ["recovery"])

    def test_orphan_recovery_focuses_exact_target_before_global_key_up(self):
        backend = FakeBackend({"fixture": 44})
        result = _recover(self.request(obligations=["key:fixture:W"],
                focus_target_before_release=True),
            backend_factory=lambda _targets: backend, clock_ns=lambda: 10,
            configured_targets={"fixture": 44})
        self.assertTrue(result["release_accepted"])
        self.assertEqual(backend.events, [("focus", "fixture"), "release"])
        self.assertEqual(backend.release_calls, 1)
        self.assertTrue(backend.closed)

    def test_recovery_generation_mismatch_sends_no_up(self):
        instances = []
        def factory(targets):
            backend = FakeBackend(targets, generation="b" * 64)
            instances.append(backend)
            return backend
        with self.assertRaisesRegex(RuntimeError, "TARGET_GENERATION_CHANGED"):
            _recover(self.request(), backend_factory=factory,
                clock_ns=lambda: 10, configured_targets={"fixture": 44})
        self.assertEqual(instances[0].release_calls, 0)
        self.assertTrue(instances[0].closed)

    def test_recovery_refuses_before_opening_backend_after_deadline(self):
        opened = []
        with self.assertRaises(TimeoutError):
            _recover(self.request(), backend_factory=lambda targets: opened.append(targets),
                clock_ns=lambda: 100, configured_targets={"fixture": 44})
        self.assertEqual(opened, [])

    def test_recovery_preserves_release_receipt_when_returned_at_deadline(self):
        backend = FakeBackend({"fixture": 44})
        times = iter((10, 10, 100))
        result = _recover(self.request(),
            backend_factory=lambda targets: backend,
            clock_ns=lambda: next(times), configured_targets={"fixture": 44})
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["reason"], "deadline_expired_after_release")
        self.assertFalse(result["release_accepted"])
        self.assertIsInstance(result["release_receipt"], dict)
        self.assertEqual(result["release_key_up_attempts"], [{
            "virtual_key": 0x11, "encoding": "virtual_key",
            "status": "returned"}])
        self.assertEqual(backend.release_calls, 1)
        self.assertTrue(backend.closed)

    def test_unicode_only_recovery_uses_configured_single_target(self):
        instances = []
        def factory(targets):
            backend = FakeBackend(targets)
            instances.append(backend)
            return backend
        result = _recover(self.request(obligations=["unicode:0041"]),
            backend_factory=factory, clock_ns=lambda: 10,
            configured_targets={"fixture": 44})
        self.assertTrue(result["release_accepted"])
        self.assertEqual(instances[0].release_snapshot,
            ({}, {}, set(), {0x41}))

    def test_unicode_only_observer_binds_readback_to_configured_generation(self):
        backend = FakeBackend({"fixture": 44})
        result = _observe(self.request(obligations=["unicode:0041"]),
            backend_factory=lambda _targets: backend, clock_ns=lambda: 50,
            configured_targets={"fixture": 44})
        self.assertTrue(result["neutral"])
        self.assertEqual(result["unicode_event_units"], 1)

    def test_observer_requires_neutral_known_key_and_button_states(self):
        backend = FakeBackend({"fixture": 44})
        result = _observe(self.request(), backend_factory=lambda _targets: backend,
            clock_ns=lambda: 50, configured_targets={"fixture": 44})
        self.assertTrue(result["neutral"])
        self.assertEqual(result["unicode_event_units"], 1)
        self.assertTrue(backend.closed)

    def test_observer_accepts_empty_obligations_for_single_configured_target(self):
        backend = FakeBackend({"fixture": 44})
        result = _observe(self.request(obligations=[]),
            backend_factory=lambda _targets: backend, clock_ns=lambda: 50,
            configured_targets={"fixture": 44})
        self.assertEqual(result["operation_id"], OPERATION)
        self.assertEqual(result["target_generation"], GENERATION)
        self.assertTrue(result["neutral"])
        self.assertEqual(result["key_button_states"], [])
        self.assertEqual(result["unicode_event_units"], 0)
        self.assertTrue(backend.closed)

    def test_observer_unknown_state_is_not_neutral(self):
        backend = FakeBackend({"fixture": 44}, states={(0x11, "fixture"): None})
        result = _observe(self.request(), backend_factory=lambda _targets: backend,
            clock_ns=lambda: 50, configured_targets={"fixture": 44})
        self.assertFalse(result["neutral"])

    def test_observer_error_does_not_claim_non_neutral_measurement(self):
        class Connection:
            def __init__(self):
                self.incoming = [self_test.request(obligations=[]), None]
                self.sent = []

            def send(self, value):
                self.sent.append(value)

            def recv(self):
                return self.incoming.pop(0)

        self_test = self
        connection = Connection()
        _helper_main("observer", {"fixture": 44, "other": 45}, connection)

        self.assertEqual(connection.sent[1]["error_type"], "ValueError")
        self.assertNotIn("neutral", connection.sent[1])
        self.assertNotIn("observed_monotonic_ns", connection.sent[1])
        self.assertEqual(connection.sent[2], {
            "control": "operation_complete", "request_id": "2" * 32})

    def test_invalid_observer_readback_remains_unknown_at_completion_boundary(self):
        class OperationOwner:
            def __init__(self):
                self.unknown = []

            def result(self, operation_id):
                return {"phase": "running", "target_generation": GENERATION,
                        "obligations": []}

            def mark_unknown(self, operation_id, generation, reason):
                self.unknown.append((operation_id, generation, reason))

        helper_error = {"operation_id": OPERATION,
            "target_generation": GENERATION, "recovery_id": "2" * 32,
            "error_type": "ValueError"}
        owner = OperationOwner()
        invalidations = []
        supervisor = object.__new__(OperationCancellationSupervisor)
        supervisor._owner = owner
        supervisor._clock_ns = lambda: 80
        supervisor._exchange_helper = lambda _role, _request, _deadline: helper_error
        supervisor._invalidate_helper = lambda role, deadline: invalidations.append(role)

        result = supervisor.observe_completed(OPERATION, GENERATION,
            producer_exit_confirmed_ns=50, deadline_ns=100)

        self.assertIsNone(result)
        self.assertEqual(len(owner.unknown), 1)
        self.assertIn("invalid_or_late", owner.unknown[0][2])
        self.assertEqual(invalidations, ["observer"])

    def test_empty_obligation_readback_is_generation_bound_at_completion(self):
        class OperationOwner:
            def __init__(self):
                self.unknown = []

            def result(self, operation_id):
                return {"phase": "running", "target_generation": GENERATION,
                        "obligations": []}

            def mark_unknown(self, operation_id, generation, reason):
                self.unknown.append((operation_id, generation, reason))

        owner = OperationOwner()
        invalidations = []
        supervisor = object.__new__(OperationCancellationSupervisor)
        supervisor._owner = owner
        supervisor._clock_ns = lambda: 80
        supervisor._exchange_helper = lambda _role, request, _deadline: _observe(
            request, backend_factory=lambda targets: FakeBackend(targets),
            clock_ns=lambda: 60, configured_targets={"fixture": 44})
        supervisor._invalidate_helper = lambda role, deadline: invalidations.append(role)

        result = supervisor.observe_completed(OPERATION, GENERATION,
            producer_exit_confirmed_ns=50, deadline_ns=100)

        self.assertEqual(result, {"operation_id": OPERATION,
            "target_generation": GENERATION,
            "producer_exit_confirmed_ns": 50,
            "observed_monotonic_ns": 60, "neutral": True})
        self.assertEqual(owner.unknown, [])
        self.assertEqual(invalidations, [])

    def test_recovery_still_rejects_empty_obligations(self):
        opened = []
        with self.assertRaisesRegex(ValueError,
                                    "native recovery requires an attributable input obligation"):
            _recover(self.request(obligations=[]),
                backend_factory=lambda targets: opened.append(targets),
                clock_ns=lambda: 10, configured_targets={"fixture": 44})
        self.assertEqual(opened, [])

    @unittest.skipUnless(os.name == "nt", "native helper startup is Windows-only")
    def test_native_components_start_helpers_before_any_operation(self):
        from runtime.cli_v1.win32_supervisor_helpers import create_native_win32_components
        with TemporaryDirectory() as output:
            owner, producer = create_native_win32_components(
                {"fixture": 1}, output)
            try:
                self.assertEqual(owner.mode, "supervised-win32")
                self.assertFalse(owner.synthetic_only)
                self.assertEqual(owner.list_results(), [])
            finally:
                self.assertEqual(owner.close()["status"], "closed")
        self.assertIsNotNone(producer)


if __name__ == "__main__":
    unittest.main()
