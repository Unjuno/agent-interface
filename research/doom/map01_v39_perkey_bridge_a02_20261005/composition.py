"""One-shot fake-display composition of V4 release batching and V12 edges."""
from __future__ import annotations

import importlib.util
import sys
import threading
import time
from pathlib import Path


DOOM = Path(__file__).resolve().parents[1]
V12 = DOOM / "map01_attack_onset_phase_allocation_02_v1" / "dependencies" / "v12"
V12_ADAPTER = DOOM / "map01_attack_onset_phase_allocation_02_v1" / "source" / "map01_v12_transition_owner.py"


def _load_adapter(owner_module):
    sys.modules["input_owner_v12"] = owner_module
    name = "map01_v12_transition_owner_v4_a02"
    spec = importlib.util.spec_from_file_location(name, V12_ADAPTER)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load frozen V12 transition adapter")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run_composition():
    """Run two distinct keys through the actual V4 methods and fake V12 owner."""
    import test_doom_retained_input_backend_v4 as v4_fixture
    from map01_v39_perkey_bridge_a01 import test_bridge

    harness_module = test_bridge.load_v12_test_harness()
    harness = harness_module.Harness(harness_module.owner_module)
    previous_owner_module = sys.modules.get("input_owner_v12")
    adapter_name = "map01_v12_transition_owner_v4_a02"
    previous_adapter = sys.modules.get(adapter_name)
    adapter_module = _load_adapter(harness_module.owner_module)
    candidate = v4_fixture.candidate
    previous_candidate_owner = candidate.InputOwner
    candidate.InputOwner = adapter_module.InputOwner

    old_keysym = harness_module.owner_module.XK.string_to_keysym
    keycodes = {"F8": 74, "SPACE": 65}
    harness_module.owner_module.XK.string_to_keysym = lambda value: keycodes[value]
    harness.d.keysym_to_keycode = lambda symbol: symbol

    operations = []
    display = harness.d
    old_query, old_sync = display.query_keymap, display.sync
    old_fake = harness_module.owner_module.xtest.fake_input

    def query_keymap():
        operations.append({"operation": "keymap-sample", "at_ns": time.perf_counter_ns()})
        return old_query()

    def sync():
        operations.append({"operation": "sync", "at_ns": time.perf_counter_ns()})
        return old_sync()

    def fake_input(target, event_type, code=None, **kwargs):
        operation = "key-down" if event_type == harness_module.X.KeyPress else "key-up"
        operations.append({"operation": operation, "at_ns": time.perf_counter_ns(),
                           "keycode": code})
        return old_fake(target, event_type, code, **kwargs)

    display.query_keymap = query_keymap
    display.sync = sync
    harness_module.owner_module.xtest.fake_input = fake_input

    class FixedOwner:
        def __new__(cls, _display_name):
            return harness.owner

    owner = None
    try:
        owner = candidate.InputOwner(":fake", _owner_cls=FixedOwner)
        lease = harness_module.Lease(intent="intent-v39-v4-a02")
        lease.interruption_snapshot = lambda: None

        backend = candidate.Backend.__new__(candidate.Backend)
        backend.owner = owner
        backend.lease = lease
        backend.held = set()
        backend._release_batch = threading.local()
        events = []
        backend.emit = events.append
        backend.execute(
            {"actions": [("F8", True), ("SPACE", True),
                         ("SPACE", False), ("F8", False)]},
            None,
            "cover-v4-a02",
            2,
        )
        return {
            "events": events,
            "operations": operations,
            "physical_keys_after": sorted(display.physical),
            "backend_held_after": sorted(backend.held),
            "fake_display_counts": {
                "keymap_queries": display.query_i,
                "sync_calls": display.sync_i,
                "injected_edges": len(display.injections),
            },
        }
    finally:
        harness_module.owner_module.xtest.fake_input = old_fake
        display.query_keymap, display.sync = old_query, old_sync
        harness_module.owner_module.XK.string_to_keysym = old_keysym
        candidate.InputOwner = previous_candidate_owner
        if owner is not None:
            owner.close()
        if previous_owner_module is None:
            sys.modules.pop("input_owner_v12", None)
        else:
            sys.modules["input_owner_v12"] = previous_owner_module
        if previous_adapter is None:
            sys.modules.pop(adapter_name, None)
        else:
            sys.modules[adapter_name] = previous_adapter
