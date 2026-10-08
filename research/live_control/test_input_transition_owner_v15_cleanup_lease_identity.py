"""A delayed batch must not join a different lease's cancellation cleanup."""
import importlib
import sys
import threading
import time
import types
import unittest


class Lease:
    def __init__(self, token):
        self.intent_token = token
        self.deadline = 424242
        self.cancel = threading.Event()
        self.interruptions = []

    def record_interruption(self, record):
        self.interruptions.append(record)


class DeferredOwner:
    def __init__(self, _display):
        self.owner_id = "synthetic-owner"
        self.records = []
        self.batch_entered = threading.Event()
        self.allow_batch_error = threading.Event()

    def close(self):
        pass

    def call(self, operation, lease=None, key=None):
        if operation == "down":
            row = {
                "event": "input_admission", "key": key, "keycode": 38,
                "admitted_ns": time.perf_counter_ns(),
                "valid_until_ns": lease.deadline,
            }
            self.records.append(row)
            return row
        if operation == "cancel":
            lease.cancel.set()
            row = {
                "event": "owner_release", "reason": "cancelled",
                "verified": True, "keys_down": [], "buttons_down": [],
                "keys_unknown": [], "key_state_errors": [],
                "verified_ns": time.perf_counter_ns(),
                "valid_until_ns": lease.deadline,
                "intent_token": lease.intent_token,
                "key_release_attempts": {
                    "38": {"verified": True,
                           "attempts": [{"server_key_down_after": False}]}
                },
            }
            self.records.append(row)
            lease.record_interruption(row)
            return row
        if operation == "up_batch":
            self.batch_entered.set()
            if not self.allow_batch_error.wait(2):
                raise TimeoutError("test did not release delayed batch")
            raise ValueError("up_batch requires the active input lease")
        raise AssertionError(operation)


class CleanupLeaseIdentityTests(unittest.TestCase):
    def test_later_same_deadline_cleanup_cannot_join_first_leases_batch(self):
        names = ("input_owner_v10", "input_owner_v12",
                 "input_transition_owner_v3", "input_transition_owner_v4")
        saved = {name: sys.modules.get(name) for name in names}
        low_level = types.ModuleType("input_owner_v10")
        low_level.InputOwner = DeferredOwner
        sys.modules["input_owner_v10"] = low_level
        sys.modules["input_owner_v12"] = low_level
        for name in names[2:]:
            sys.modules.pop(name, None)
        owner_class = importlib.import_module("input_transition_owner_v4").InputOwner
        owner = owner_class(":fake", _owner_cls=DeferredOwner)
        first = Lease("intent-first")
        later = Lease("intent-later")
        result = []

        def delayed_batch():
            try:
                result.extend(owner.call("up_batch", first, ["W"]))
            except BaseException as exc:
                result.append(exc)

        worker = threading.Thread(target=delayed_batch)
        try:
            owner.call("down", first, "W")
            worker.start()
            self.assertTrue(owner._inner.batch_entered.wait(1))

            # The first cancellation has already released W. A subsequent
            # lease reuses the same deadline and key, then also gets cancelled
            # before the delayed caller inspects the owner's shared history.
            owner.call("cancel", first)
            owner.call("down", later, "W")
            owner.call("cancel", later)
            owner._inner.allow_batch_error.set()
            worker.join(2)
            self.assertFalse(worker.is_alive())
            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0], ValueError)
        finally:
            owner._inner.allow_batch_error.set()
            if worker.is_alive():
                worker.join(2)
            owner.close()
            for name, module in saved.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module


if __name__ == "__main__":
    unittest.main()
