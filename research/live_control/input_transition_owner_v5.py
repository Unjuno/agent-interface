"""Opt-in per-key X-server state sampling for the V39 measurement path."""

from input_owner_v12 import InputOwner as OwnerWithKeymapSample
from input_transition_owner_v4 import InputOwner as Previous


class _SampledOwner(OwnerWithKeymapSample):
    def __init__(self, display_name):
        super().__init__(display_name, sample_keymap_after_each_explicit_up=True)


class InputOwner(Previous):
    """V4 receipt join with the V12 owner configured to sample after each up."""

    def __init__(self, display_name):
        super().__init__(display_name, _owner_cls=_SampledOwner)

    def call(self, operation, lease=None, key=None):
        result = super().call(operation, lease, key)
        if operation != "up" or not isinstance(result, dict):
            return result
        receipt = result.get("owner_thread_keyup_receipt")
        if not isinstance(receipt, dict):
            return result
        result = dict(result)
        result.update({
            "owner_keymap_sample_available": receipt.get("owner_keymap_sample_available"),
            "owner_keymap_state_after_release": receipt.get("owner_keymap_state_after_release"),
            "owner_keycode_down_after_release": receipt.get("owner_keycode_down_after_release"),
            "owner_keymap_sample_started_ns": receipt.get("owner_keymap_sample_started_ns"),
            "owner_keymap_sample_finished_ns": receipt.get("owner_keymap_sample_finished_ns"),
            "owner_keymap_sample_error_type": receipt.get("owner_keymap_sample_error_type"),
        })
        result["ordinary_release_candidate"] = (
            result.get("ordinary_release_candidate") is True
            and receipt.get("owner_keymap_sample_available") is True
            and receipt.get("owner_keymap_state_after_release") == "UP"
        )
        return result


