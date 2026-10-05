import sys
import types
import unittest
from unittest.mock import patch


HERE = __import__("pathlib").Path(__file__).resolve().parent


class OwnerReceiptJoinTests(unittest.TestCase):
    def test_join_reads_live_underlying_owner_history_and_bounds_it_by_caller(self):
        owner_module = types.ModuleType("input_owner_v12")
        transition_module = types.ModuleType("input_transition_owner_v3")

        class Owner:
            def __init__(self, display_name):
                self.owner_id = "owner-1"
                self.records = []

            def close(self):
                pass

            def call(self, operation, lease=None, key=None):
                if operation == "up":
                    self.records.append({
                        "event": "owner_explicit_keyup", "operation": "up", "key": key,
                        "owner_id": self.owner_id, "intent_token": lease.intent_token,
                        "valid_until_ns": lease.deadline,
                        "owner_keyrelease_started_ns": 12, "owner_sync_returned_ns": 13,
                        "owner_keymap_sampled_ns": 14,
                        "server_keyup_verified": True,
                        "server_key_down_after_keyup": False,
                        "server_keyup_attempt_count": 1,
                        "server_keyup_attempts": [{"attempt": 1,
                            "keyrelease_started_ns": 12, "sync_returned_ns": 13,
                            "keymap_sampled_ns": 14,
                            "server_key_down_before": True,
                            "server_key_down_after": False}],
                        "key_state_source": "x11_query_keymap",
                        "cancel_requested_after_sync": False,
                        "server_sync_completed": True,
                        "physical_verification_authoritative": False,
                    })
                    return None
                raise AssertionError(operation)

        owner_module.InputOwner = Owner

        class Previous:
            @staticmethod
            def _intent_token(lease):
                return getattr(lease, "intent_token", None)

            def __init__(self, display_name, _owner_cls=Owner):
                self._inner = _owner_cls(display_name)

            @property
            def owner_id(self):
                return self._inner.owner_id

            @property
            def records(self):
                return list(self._inner.records)

            def call(self, operation, lease=None, key=None):
                started = 10
                self._inner.call(operation, lease, key)
                returned = 15
                return {
                    "event": "input_release_transition", "operation": operation,
                    "key": key, "owner_id": self.owner_id,
                    "intent_token": lease.intent_token, "valid_until_ns": lease.deadline,
                    "release_call_started_ns": started,
                    "release_call_returned_ns": returned,
                    "ordinary_release_candidate": True,
                }

        transition_module.InputOwner = Previous
        saved_owner = sys.modules.get("input_owner_v12")
        saved_transition = sys.modules.get("input_transition_owner_v3")
        sys.modules["input_owner_v12"] = owner_module
        sys.modules["input_transition_owner_v3"] = transition_module
        sys.path.insert(0, str(HERE))
        try:
            import input_transition_owner_v4 as candidate
            with patch.object(candidate, "OwnerWithKeyUpReceipt", Owner):
                wrapper = candidate.InputOwner("display")
            lease = types.SimpleNamespace(intent_token="lease-2", deadline=99)
            receipt = wrapper.call("up", lease, "w")
            self.assertTrue(receipt["owner_thread_keyup_verified"])
            self.assertEqual(receipt["owner_thread_keyup_receipt_count"], 1)
            self.assertTrue(receipt["ordinary_release_candidate"])
        finally:
            sys.path.remove(str(HERE))
            sys.modules.pop("input_transition_owner_v4", None)
            if saved_owner is None:
                sys.modules.pop("input_owner_v12", None)
            else:
                sys.modules["input_owner_v12"] = saved_owner
            if saved_transition is None:
                sys.modules.pop("input_transition_owner_v3", None)
            else:
                sys.modules["input_transition_owner_v3"] = saved_transition

    def test_up_batch_join_preserves_exact_input_admission_receipt(self):
        owner_module = types.ModuleType("input_owner_v12")
        transition_module = types.ModuleType("input_transition_owner_v3")
        admission = {
            "event": "input_admission", "key": "w", "owner_id": "owner-1",
            "intent_token": "intent-2", "valid_until_ns": 99,
            "admitted_ns": 2, "input_ack_ns": 3,
        }
        keyup = {
            "event": "owner_explicit_keyup", "operation": "up", "key": "w",
            "owner_id": "owner-1", "intent_token": "intent-2", "valid_until_ns": 99,
            "owner_keyrelease_started_ns": 11, "owner_sync_returned_ns": 12,
            "owner_keymap_sampled_ns": 13, "server_keyup_verified": True,
            "server_key_down_after_keyup": False, "server_keyup_attempt_count": 1,
            "server_keyup_attempts": [{"attempt": 1, "keyrelease_started_ns": 11,
                "sync_returned_ns": 12, "keymap_sampled_ns": 13,
                "server_key_down_before": True, "server_key_down_after": False}],
            "key_state_source": "x11_query_keymap", "cancel_requested_after_sync": False,
            "server_sync_completed": True, "physical_verification_authoritative": False,
            "release_batch_initial_up_count": 1, "release_batch_key_order": ["w"],
        }

        class Owner:
            def __init__(self, display_name):
                self.owner_id = "owner-1"
                self.records = []

            def close(self):
                pass

            def call(self, operation, lease=None, key=None):
                if operation == "up_batch":
                    self.records.append(keyup)
                    return [keyup]
                raise AssertionError(operation)

        owner_module.InputOwner = Owner

        class Previous:
            @staticmethod
            def _intent_token(lease):
                return getattr(lease, "intent_token", None)

            def __init__(self, display_name, _owner_cls=Owner):
                self._inner = _owner_cls(display_name)

            @property
            def owner_id(self):
                return self._inner.owner_id

            @property
            def records(self):
                return list(self._inner.records)

            def call(self, operation, lease=None, key=None):
                self._inner.call(operation, lease, key)
                return [{
                    "event": "input_release_transition", "operation": "up", "key": "w",
                    "owner_id": self.owner_id, "intent_token": lease.intent_token,
                    "valid_until_ns": lease.deadline, "release_call_started_ns": 10,
                    "release_call_returned_ns": 20, "ordinary_release_candidate": True,
                    "admission_receipt": dict(admission),
                    "admission_receipt_valid": True,
                }]

        transition_module.InputOwner = Previous
        saved_owner = sys.modules.get("input_owner_v12")
        saved_transition = sys.modules.get("input_transition_owner_v3")
        sys.modules["input_owner_v12"] = owner_module
        sys.modules["input_transition_owner_v3"] = transition_module
        sys.path.insert(0, str(HERE))
        try:
            import input_transition_owner_v4 as candidate
            with patch.object(candidate, "OwnerWithKeyUpReceipt", Owner):
                wrapper = candidate.InputOwner("display")
            lease = types.SimpleNamespace(intent_token="intent-2", deadline=99)
            rows = wrapper.call("up_batch", lease, ["w"])
            self.assertEqual(len(rows), 1)
            self.assertTrue(rows[0]["owner_thread_keyup_verified"])
            self.assertTrue(rows[0]["admission_receipt_valid"])
            self.assertEqual(rows[0]["admission_receipt"], admission)
        finally:
            sys.path.remove(str(HERE))
            sys.modules.pop("input_transition_owner_v4", None)
            if saved_owner is None:
                sys.modules.pop("input_owner_v12", None)
            else:
                sys.modules["input_owner_v12"] = saved_owner
            if saved_transition is None:
                sys.modules.pop("input_transition_owner_v3", None)
            else:
                sys.modules["input_transition_owner_v3"] = saved_transition


if __name__ == "__main__":
    unittest.main()
