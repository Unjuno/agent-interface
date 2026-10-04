"""Bridge the V13 RPC-returning owner to the V4 transition-returning contract.

V13's release RPC receipt is consumed by this adapter and retained inside the
V4 transition row. The V4 parent therefore still receives None from its inner
owner call, while both caller intervals and the V13 receipt remain available
for downstream release-batch evidence.
"""
from __future__ import annotations

import threading


def _rpc_matches_transition(receipt, transition, operation, key):
    if type(receipt) is not dict or receipt.get("event") != "input_release_rpc":
        return False
    if type(transition) is not dict or transition.get("event") != "input_release_transition":
        return False
    started = receipt.get("call_started_ns")
    returned = receipt.get("call_returned_ns")
    outer_started = transition.get("release_call_started_ns")
    outer_returned = transition.get("release_call_returned_ns")
    return bool(
        receipt.get("operation") == operation
        and receipt.get("payload") == key
        and receipt.get("owner_id") == transition.get("owner_id")
        and receipt.get("intent_token") == transition.get("intent_token")
        and receipt.get("valid_until_ns") == transition.get("valid_until_ns")
        and type(started) is int and type(returned) is int
        and type(outer_started) is int and type(outer_returned) is int
        and outer_started <= started <= returned <= outer_returned
        and receipt.get("release_transition_interval_ns") == [started, returned]
        and receipt.get("x11_release_and_sync_completed_before_return") is True
        and receipt.get("continuous_physical_state_sampled") is False
        and receipt.get("application_consumption_observed") is False
        and receipt.get("grants_input_authority") is False
    )


def bind_v13_to_v4(transition_owner_cls, v13_owner_cls):
    """Return a V4 owner class backed by V13 without losing either receipt."""
    class RpcReturningOwnerAdapter:
        def __init__(self, display_name, owner_cls=v13_owner_cls):
            self._inner = owner_cls(display_name)
            self._rpc_lock = threading.Lock()
            self._rpc_receipts = []

        @property
        def owner_id(self):
            return self._inner.owner_id

        @property
        def records(self):
            return self._inner.records

        def close(self):
            return self._inner.close()

        def call(self, operation, lease=None, key=None):
            result = self._inner.call(operation, lease, key)
            if (operation in ("up", "button_up") and type(result) is dict
                    and result.get("event") == "input_release_rpc"):
                with self._rpc_lock:
                    self._rpc_receipts.append(result)
                # The V4 transition wrapper requires the v10 None-return API.
                return None
            return result

        def take_rpc(self, operation, key):
            with self._rpc_lock:
                matches = [index for index, row in enumerate(self._rpc_receipts)
                           if row.get("operation") == operation
                           and row.get("payload") == key]
                if len(matches) != 1:
                    self._rpc_receipts = [row for row in self._rpc_receipts
                                          if not (row.get("operation") == operation
                                                  and row.get("payload") == key)]
                    return None
                return self._rpc_receipts.pop(matches[0])

        def discard_rpc(self, operation, key):
            with self._rpc_lock:
                self._rpc_receipts = [row for row in self._rpc_receipts
                                      if not (row.get("operation") == operation
                                              and row.get("payload") == key)]

    class InputOwnerV13V4Bridge(transition_owner_cls):
        def __init__(self, display_name, _v13_owner_cls=v13_owner_cls):
            class ConfiguredOwnerAdapter(RpcReturningOwnerAdapter):
                def __init__(self, configured_display_name):
                    super().__init__(configured_display_name, _v13_owner_cls)
            super().__init__(display_name, _owner_cls=ConfiguredOwnerAdapter)

        def call(self, operation, lease=None, key=None):
            try:
                transition = super().call(operation, lease, key)
            except BaseException:
                if operation in ("up", "button_up"):
                    self._inner.discard_rpc(operation, key)
                raise
            if (operation not in ("up", "button_up") or type(transition) is not dict
                    or transition.get("event") != "input_release_transition"):
                return transition
            receipt = self._inner.take_rpc(operation, key)
            valid = _rpc_matches_transition(receipt, transition, operation, key)
            result = dict(transition)
            result["v13_release_rpc_receipt"] = dict(receipt) if type(receipt) is dict else None
            result["v13_release_rpc_receipt_valid"] = valid
            result["ordinary_release_candidate"] = (
                transition.get("ordinary_release_candidate") is True and valid
            )
            result["release_measurement_contract_v13_v4"] = (
                "V13 RPC interval is nested in the V4 caller transition; V4 also retains "
                "the exact owner-thread key-up/XSync receipt; neither proves app consumption"
            )
            return result

    return InputOwnerV13V4Bridge
