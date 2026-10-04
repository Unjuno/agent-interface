"""Characterize the #7429 V13 RPC receipt to #7449 V4 release contract."""
import importlib.util
import json
import os
import sys
import threading
import time
import types
import unittest
from pathlib import Path
from unittest.mock import patch

candidate = Path(__file__).resolve().parent
exact = candidate / "input_transition_owner_v4-pr7488-frozen-exact.py"
exact_v3 = candidate / "input_transition_owner_v3-pr7488-frozen-exact.py"
exact_batch_backend = candidate / "backend-v3-pr7449-exact.py"
exact_batch_backend_current = candidate / "backend-v1-pr7488-exact.py"
exact_v13 = candidate / "input_owner_v13-pr7429-exact.py"
exact_v11 = candidate / "input_owner_v11-pr7429-exact.py"
bridge_path = candidate / "input_owner_v13_v4_bridge.py"


def load_source(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_exact_v4():
    owner_v10 = types.ModuleType("input_owner_v10")
    owner_v10.InputOwner = object
    owner_v12 = types.ModuleType("input_owner_v12")
    owner_v12.InputOwner = object
    with patch.dict(sys.modules, {"input_owner_v10": owner_v10,
                                  "input_owner_v12": owner_v12}):
        v3 = load_source("bridge_probe_transition_v3", exact_v3)
        with patch.dict(sys.modules, {"input_transition_owner_v3": v3}):
            v4 = load_source("bridge_probe_transition_v4", exact)
    return v4.InputOwner


def load_exact_v13_call_class():
    base_owner = type("InputOwnerV10Stub", (), {})
    owner_v10 = types.ModuleType("input_owner_v10")
    owner_v10.InputOwner = base_owner
    executor_v3 = types.ModuleType("executor_v3")
    executor_v3.Cancelled = type("Cancelled", (Exception,), {})
    executor_v3.DecisionRequired = type("DecisionRequired", (Exception,), {})
    xlib = types.ModuleType("Xlib")
    xlib.__path__ = []
    xlib.X = object()
    xlib.XK = object()
    xlib.display = object()
    xlib.error = object()
    xlib_ext = types.ModuleType("Xlib.ext")
    xlib_ext.xtest = object()
    with patch.dict(sys.modules, {"input_owner_v10": owner_v10,
                                  "executor_v3": executor_v3,
                                  "Xlib": xlib, "Xlib.ext": xlib_ext}):
        v11 = load_source("bridge_probe_input_owner_v11", exact_v11)
        with patch.dict(sys.modules, {"input_owner_v11": v11}):
            v13 = load_source("bridge_probe_input_owner_v13", exact_v13)
    return base_owner, v13.InputOwner


class Lease:
    def __init__(self):
        self.deadline = time.perf_counter_ns() + 1_000_000_000
        self.intent_token = "intent-bridge"
        self.cancel = threading.Event()
        self.focus_invalid = False


class FakeV13Owner:
    rpc_token = "intent-bridge"
    omit_rpc = False

    def __init__(self, display_name):
        self.display_name = display_name
        self.owner_id = "owner-v13-bridge"
        self.records = []
        self.calls = []

    def call(self, operation, lease=None, key=None):
        self.calls.append((operation, lease, key))
        if operation != "up":
            return None
        rpc_started = time.perf_counter_ns()
        owner_started = time.perf_counter_ns()
        owner_returned = time.perf_counter_ns()
        rpc_returned = time.perf_counter_ns()
        self.records.append({
            "event": "owner_explicit_keyup", "operation": "up", "key": key,
            "owner_id": self.owner_id, "intent_token": lease.intent_token,
            "valid_until_ns": lease.deadline,
            "owner_keyrelease_started_ns": owner_started,
            "owner_sync_returned_ns": owner_returned,
            "server_sync_completed": True,
            "physical_verification_authoritative": False,
        })
        if self.omit_rpc:
            return None
        return {
            "event": "input_release_rpc", "operation": "up", "payload": key,
            "owner_id": self.owner_id, "intent_token": self.rpc_token,
            "valid_until_ns": lease.deadline,
            "call_started_ns": rpc_started, "call_returned_ns": rpc_returned,
            "release_transition_interval_ns": [rpc_started, rpc_returned],
            "x11_release_and_sync_completed_before_return": True,
            "continuous_physical_state_sampled": False,
            "application_consumption_observed": False,
            "grants_input_authority": False,
        }

    def close(self):
        return None


class TransitionV4RpcBridgeTests(unittest.TestCase):
    def bridge_class(self):
        if not bridge_path.exists():
            self.fail("V13-to-V4 release contract bridge is not implemented")
        from input_owner_v13_v4_bridge import bind_v13_to_v4
        return bind_v13_to_v4(load_exact_v4(), FakeV13Owner)

    def test_rpc_receipt_is_consumed_but_v4_transition_and_keyup_join_survive(self):
        owner = self.bridge_class()("DISPLAY")
        lease = Lease()
        result = owner.call("up", lease, "A")

        self.assertEqual(result["event"], "input_release_transition")
        self.assertEqual(result["transition_schema"], "input-release-transition-v3")
        self.assertTrue(result["owner_thread_keyup_verified"])
        self.assertEqual(result["v13_release_rpc_receipt"]["event"], "input_release_rpc")
        self.assertTrue(result["v13_release_rpc_receipt_valid"])
        self.assertTrue(result["ordinary_release_candidate"])
        self.assertEqual(owner._inner._inner.calls[0], ("up", lease, "A"))

    def test_bad_or_missing_rpc_receipt_disqualifies_ordinary_release(self):
        for owner_cls in (type("WrongTokenOwner", (FakeV13Owner,),
                               {"rpc_token": "other-intent"}),
                          type("MissingRpcOwner", (FakeV13Owner,), {"omit_rpc": True})):
            with self.subTest(owner_cls=owner_cls.__name__):
                owner = self.bridge_class()("DISPLAY", _v13_owner_cls=owner_cls)
                result = owner.call("up", Lease(), "A")
                self.assertEqual(result["event"], "input_release_transition")
                self.assertFalse(result["v13_release_rpc_receipt_valid"])
                self.assertFalse(result["ordinary_release_candidate"])

    def test_exact_v13_v11_call_path_is_consumed_by_exact_v4_parent(self):
        base_owner, exact_owner_v13 = load_exact_v13_call_class()

        class TestV13Owner(exact_owner_v13):
            def __init__(self, display_name):
                self.owner_id = "owner-v13-exact"
                self.records = []

            def close(self):
                return None

        def fake_v10_call(self, operation, lease=None, key=None):
            if operation == "up":
                started = time.perf_counter_ns()
                returned = time.perf_counter_ns()
                self.records.append({
                    "event": "owner_explicit_keyup", "operation": "up", "key": key,
                    "owner_id": self.owner_id, "intent_token": lease.intent_token,
                    "valid_until_ns": lease.deadline,
                    "owner_keyrelease_started_ns": started,
                    "owner_sync_returned_ns": returned,
                    "server_sync_completed": True,
                    "physical_verification_authoritative": False,
                })
            return None

        owner_type = self.bridge_class()
        owner = owner_type("DISPLAY", _v13_owner_cls=TestV13Owner)
        with patch.object(base_owner, "call", fake_v10_call, create=True):
            result = owner.call("up", Lease(), "A")

        self.assertEqual(result["event"], "input_release_transition")
        self.assertTrue(result["owner_thread_keyup_verified"])
        self.assertTrue(result["v13_release_rpc_receipt_valid"])
        self.assertEqual(result["v13_release_rpc_receipt"]["event"],
                         "input_release_rpc")
        self.assertTrue(result["ordinary_release_candidate"])

    def test_exact_v4_release_batch_backends_accept_and_fail_closed(self):
        base_owner, exact_owner_v13 = load_exact_v13_call_class()

        class TestV13Owner(exact_owner_v13):
            def __init__(self, display_name):
                self.owner_id = "owner-v13-backend"
                self.records = []

            def close(self):
                return None

        class WrongTokenV13Owner(TestV13Owner):
            def call(self, operation, lease=None, key=None):
                receipt = super().call(operation, lease, key)
                if operation == "up" and type(receipt) is dict:
                    receipt["intent_token"] = "foreign-intent"
                return receipt

        def fake_v10_call(self, operation, lease=None, key=None):
            if operation == "up":
                started = time.perf_counter_ns()
                returned = time.perf_counter_ns()
                self.records.append({
                    "event": "owner_explicit_keyup", "operation": "up", "key": key,
                    "owner_id": self.owner_id, "intent_token": lease.intent_token,
                    "valid_until_ns": lease.deadline,
                    "owner_keyrelease_started_ns": started,
                    "owner_sync_returned_ns": returned,
                    "server_sync_completed": True,
                    "physical_verification_authoritative": False,
                })
                return None
            if operation == "input_state":
                sample_started = time.perf_counter_ns()
                sample_finished = time.perf_counter_ns()
                return {
                    "owner_id": self.owner_id, "owned_keycodes": [],
                    "sample_started_ns": sample_started,
                    "sample_finished_ns": sample_finished,
                }
            raise AssertionError(f"unexpected owner operation: {operation}")

        from input_owner_v13_v4_bridge import bind_v13_to_v4
        base_v2 = types.ModuleType("doom_typed_release_backend_v2")
        base_v2.suite = object()
        class PriorBackend:
            def __init__(self, session, out, emit, signal_readers):
                class OldOwner:
                    def close(self):
                        return None
                self.owner = OldOwner()
                self.emit = emit
                self.held = set()

            def execute(self, step, cancel, identifier, index):
                self.lease = Lease()
                self._input_event_context = (identifier, index)
                self.held.add("A")
                self.raw("A", False)
                self._input_event_context = None
                return {"ok": True}

        base_v2.Backend = PriorBackend
        v4_module = types.ModuleType("input_transition_owner_v4")
        for owner_name, owner_cls, expected_valid in (
                ("valid_rpc", TestV13Owner, True),
                ("wrong_rpc_token", WrongTokenV13Owner, False)):
            v4_module.InputOwner = bind_v13_to_v4(load_exact_v4(), owner_cls)
            for backend_name, backend_path in (
                    ("pr7449_v3", exact_batch_backend),
                    ("pr7488_v1", exact_batch_backend_current)):
                with self.subTest(owner=owner_name, backend=backend_name):
                    with patch.dict(sys.modules, {
                            "doom_typed_release_backend_v2": base_v2,
                            "input_transition_owner_v4": v4_module}):
                        backend_module = load_source(
                            "bridge_probe_release_batch_backend_" + backend_name,
                            backend_path)

                    emitted = []
                    with patch.object(base_owner, "call", fake_v10_call, create=True):
                        backend = backend_module.Backend(
                            types.SimpleNamespace(name="DISPLAY"), None, emitted.append, None)
                        backend.owner.close = lambda: None
                        result = backend.execute(None, None, "request-1", 0)

                    self.assertEqual(result, {"ok": True})
                    self.assertEqual(len(emitted), 1)
                    self.assertEqual(emitted[0]["event"], "input_release_transition")
                    self.assertEqual(emitted[0]["v13_release_rpc_receipt_valid"],
                                     expected_valid)
                    self.assertEqual(emitted[0]["ordinary_release_candidate"],
                                     expected_valid)
                    self.assertEqual(emitted[0]["release_batch_schema"],
                                     "input-release-batch-v3")
                    self.assertEqual(emitted[0]["owner_transition_verified"],
                                     expected_valid)
                    self.assertTrue(emitted[0]["owner_thread_keyup_verified_after_batch"])
                    trace_path = os.environ.get("BRIDGE_TRACE_OUTPUT")
                    if trace_path and backend_name == "pr7488_v1" and expected_valid:
                        target = Path(trace_path)
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_text(
                            json.dumps(emitted[0], indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")


if __name__ == "__main__":
    unittest.main(verbosity=2)
