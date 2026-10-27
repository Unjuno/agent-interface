"""G10 caller/core/shared-guard composition over real bridge with Fake X transport.

This is a deterministic integration seam: NativeHandleBridge, X11 session,
guarded compiled adapter and caller are real; only the X transport/application
effect are simulated. It is not live Calc or an independent effect result.
"""
import copy
import json
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from pathlib import Path

from PIL import Image
from Xlib import X

from runtime.cli_v1.test_mcp_process_identity import FakeX
from runtime.guarded_x11_v1.bridge import NativeHandleBridge
from research.integration.test_calc_g10_fresh_admission_v1 import (
    bindings as g10_bindings, interface as retained_g10_interface,
)
from research.live_control import calc_g10_fresh_admission_v1 as fresh_admission
from research.live_control.calc_bounded_proposal_v1 import BoundedProposal
from research.live_control.calc_g10_caller_v1 import run_g10_in_caller


class G10NativeCallerCompositionTests(unittest.TestCase):
    def run_case(self, *, unknown_first_effect=False, delay_proposal=False):
        fake = FakeX(self)
        buttons, pointer = set(), [0, 0]
        fake.backend.root.query_pointer = lambda: type("Pointer", (), {
            "mask": X.Button1Mask if buttons else 0,
            "root_x": pointer[0], "root_y": pointer[1],
        })()

        def emit(_display, kind, code=0, **kwargs):
            fake.emissions.append((kind, code, copy.deepcopy(kwargs)))
            if kind == X.MotionNotify:
                pointer[:] = [kwargs.get("x", pointer[0]), kwargs.get("y", pointer[1])]
            elif kind == X.ButtonPress:
                buttons.add(code)
            elif kind == X.ButtonRelease:
                buttons.discard(code)
            else:
                fake.emit(_display, kind, code)

        from runtime.backends.x11_v1 import backend as x11_backend
        x11_backend.xtest.fake_input.side_effect = emit
        state = {"clicks": 0, "old_alias_status": None, "outer_score": 0,
                 "published": [], "target_builds": []}
        proposal_entered, release_proposal, proposal_completed = (
            threading.Event(), threading.Event(), threading.Event())
        cancelled = lambda: False

        def set_frame(marker, *, invalidate=False):
            image = Image.frombytes("RGB", (32, 32), fake.raw, "raw", "BGRX")
            image.putpixel((31, 31), (marker, 0, 0))
            if invalidate:
                image.putpixel((8, 8), (255, 255, 255))
            fake.raw = image.tobytes("raw", "BGRX")

        with tempfile.TemporaryDirectory(prefix="calc-g10-native-caller-") as tmp:
            bridge = NativeHandleBridge(None, {"app": 20}, "app", Path(tmp) / "bridge")
            try:
                initial = bridge.observe()
                bridge.mint_reference("a1_primary", initial["sequence"], [8, 8],
                                      region_size=(12, 12))

                original_click = bridge.click

                def click_and_change(*args, **kwargs):
                    result = original_click(*args, **kwargs)
                    state["clicks"] += 1
                    if state["clicks"] == 1:
                        set_frame(3 if unknown_first_effect else 1, invalidate=True)
                    else:
                        set_frame(2)
                    return result

                bridge.click = click_and_change

                def perceive(native, image):
                    marker = image.getpixel((31, 31))[0]
                    row_visible = "unknown" if unknown_first_effect and marker == 3 else marker > 0
                    return {"ready": True, "row_visible": row_visible}

                def proposal(native, image):
                    stale = bridge.store.resolve_point(
                        "a1_primary", [6, 6], native, image, time.monotonic_ns(),
                        session_scope=bridge.scope)
                    state["old_alias_status"] = stale["status"]
                    candidate = {"alias": "a1_second", "source_sequence": native["sequence"],
                                 "source_sha256": native["native"]["artifact"]["sha256"],
                                 "point": [8, 8], "region_size": [12, 12]}
                    if delay_proposal:
                        proposal_entered.set()
                        release_proposal.wait(1)
                        proposal_completed.set()
                    return candidate

                proposal_worker = BoundedProposal(
                    proposal, timeout_ms=30 if delay_proposal else 500, cancelled=cancelled)
                graph = retained_g10_interface()
                graph["session_scope"] = bridge.scope
                graph["surface"] = "x11-window-20"
                graph["symbols"]["anchor"]["target_reference"] = "a1_primary"
                graph["symbols"]["second_anchor"] = copy.deepcopy(graph["symbols"]["anchor"])
                graph["symbols"]["second_anchor"]["target_reference"] = "a1_second"
                graph["actions"]["second"]["target_symbol"] = "second_anchor"
                action_bindings = g10_bindings()
                action_bindings = {name: dict(binding, offset=[6, 6])
                                   for name, binding in action_bindings.items()}

                def build_for_final_target(payload):
                    state["target_builds"].append(payload["target"]["id"])
                    return graph

                def compiled_effect(request, _native, _image):
                    status = request["observation"]["predicates"]["row_visible"]
                    return {"status": "succeeded" if status is True else "unavailable",
                            "evidence_ref": request["observation"]["evidence_ref"]}

                def outer_effect(_request):
                    state["outer_score"] += 1
                    return {"status": "succeeded", "evidence_ref": "synthetic-outer-effect"}

                spec = {"target": "calc", "route": "reuse", "coarse_origin": "caller_provided",
                        "provided_coarse": None, "cached_target": {"id": "old"},
                        "repair_on": [], "local_repair_on": [], "session_id": "native-fake-x"}
                caller_adapters = {
                    "reuse_revalidate": lambda _: {"status": "revalidated"},
                    "final_revalidate": lambda _: {"status": "revalidated",
                                                    "target": {"id": "new"}},
                    "verify_effect": outer_effect,
                    "journal": lambda _: None,
                }
                # The strict post-action capture gate compares monotonic
                # timestamps. Advance the fixture clock between calls so the
                # intended fresh-capture case is deterministic on hosts whose
                # monotonic clock has a coarse tick.
                clock_state = {"ns": time.monotonic_ns()}
                def advance_clock():
                    clock_state["ns"] += 1_000_000
                    return clock_state["ns"]
                original_mint = fresh_admission.mint_from_proposal
                def record_freshness_gate(native_bridge, proposal, *, scope, after_ns):
                    capture_ns = native_bridge.history[proposal["source_sequence"]][0]["capture_ns"]
                    state["freshness_gate"] = {"action_return_ns": after_ns,
                                                "capture_ns": capture_ns}
                    return original_mint(native_bridge, proposal, scope=scope,
                                         after_ns=after_ns)
                with patch("time.monotonic_ns", side_effect=advance_clock), patch.object(
                        fresh_admission, "mint_from_proposal",
                        side_effect=record_freshness_gate):
                    result = run_g10_in_caller(
                        spec, caller_adapters, build_for_final_target, bridge, action_bindings,
                        perceive=perceive, verify_effect=compiled_effect,
                        proposal_worker=proposal_worker, cancelled=cancelled,
                        on_receipt=lambda receipt: state["published"].append(copy.deepcopy(receipt)))
                if proposal_worker.thread is not None and not delay_proposal:
                    proposal_worker.thread.join(1)
                state["worker"] = proposal_worker.snapshot()
                if delay_proposal:
                    state["proposal_entered"] = proposal_entered
                    state["release_proposal"] = release_proposal
                    state["proposal_completed"] = proposal_completed
                    state["proposal_worker"] = proposal_worker
                state["native_executions"] = [
                    json.loads(path.read_text(encoding="utf-8"))
                    for path in Path(tmp, "bridge").glob("result-*.json")
                ]
                state["physical_down"] = sorted(fake.down)
                state["emissions"] = list(fake.emissions)
                state["used_aliases"] = sorted(bridge.used_aliases)
                return bridge, state, result
            finally:
                bridge.close()

    def test_success_uses_fresh_native_alias_and_publishes_task_receipt_once(self):
        bridge, state, result = self.run_case()
        self.assertEqual(result["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(result["compiled_execution_receipt"]["completed_transitions"], 2)
        self.assertEqual(state["old_alias_status"], "MISSING")
        self.assertEqual(state["used_aliases"], ["a1_primary", "a1_second"])
        self.assertEqual(state["target_builds"], ["new"])
        self.assertEqual((state["clicks"], state["outer_score"], len(state["published"])), (2, 1, 1))
        self.assertLess(state["freshness_gate"]["action_return_ns"],
                        state["freshness_gate"]["capture_ns"], state["freshness_gate"])
        self.assertEqual(len(state["native_executions"]), 2)
        self.assertTrue(all(row["status"] == "completed" and row["admission"] == "accepted"
                            and row["execution"]["releases"]
                            and row["execution"]["releases"][-1]["verified"] is True
                            and row["execution"]["releases"][-1]["keys_down"] == []
                            and row["execution"]["releases"][-1]["buttons_down"] == []
                            for row in state["native_executions"]))
        self.assertEqual([event[0] for event in state["emissions"]],
                         [X.MotionNotify, X.ButtonPress, X.ButtonRelease] * 2)
        self.assertEqual(state["worker"], {"used": True, "retired": True, "thread_alive": False})
        self.assertEqual(state["physical_down"], [])
        self.assertTrue(bridge.session.recovery_required is False)
        self.assertTrue(bridge._input_guard is None)
        terminals = [event for event in result["compiled_execution_receipt"]["critical_events"]
                     if event["event"] == "action_terminal"]
        self.assertEqual(len(terminals), 2)
        self.assertTrue(all(event["release_verified"] for event in terminals))

    def test_unknown_first_effect_keeps_prefix_and_skips_second_input_and_outer_score(self):
        _, state, result = self.run_case(unknown_first_effect=True)
        self.assertEqual(result["outcome"], "EXECUTION_INCOMPLETE")
        self.assertEqual(result["compiled_execution_receipt"]["completed_transitions"], 1)
        self.assertEqual((state["clicks"], state["outer_score"], len(state["published"])), (1, 0, 1))
        self.assertEqual(state["physical_down"], [])
        self.assertEqual(len(state["native_executions"]), 1)
        self.assertTrue(state["native_executions"][0]["execution"]["releases"][-1]["verified"])
        self.assertEqual(state["worker"]["used"], False)


    def test_late_proposal_after_deadline_keeps_release_and_never_dispatches_second_input(self):
        bridge, state, result = self.run_case(delay_proposal=True)
        release = state["release_proposal"]
        worker = state["proposal_worker"]
        try:
            self.assertTrue(state["proposal_entered"].is_set())
            self.assertEqual(result["outcome"], "EXECUTION_INCOMPLETE")
            receipt = result["compiled_execution_receipt"]
            self.assertEqual(receipt["completed_transitions"], 1)
            self.assertEqual(state["old_alias_status"], "MISSING")
            self.assertEqual(state["clicks"], 1)
            self.assertEqual(state["outer_score"], 0)
            self.assertEqual(len(state["published"]), 1)
            self.assertEqual(len(state["native_executions"]), 1)
            first = state["native_executions"][0]
            self.assertEqual(first["status"], "completed")
            self.assertTrue(first["execution"]["releases"][-1]["verified"])
            self.assertEqual(first["execution"]["releases"][-1]["keys_down"], [])
            self.assertEqual(first["execution"]["releases"][-1]["buttons_down"], [])
            self.assertEqual(state["physical_down"], [])
            self.assertEqual(state["used_aliases"], ["a1_primary"])
            self.assertTrue(state["worker"]["retired"])
            self.assertTrue(state["worker"]["thread_alive"])
            release.set()
            worker.thread.join(1)
            self.assertTrue(state["proposal_completed"].is_set())
            self.assertFalse(worker.thread.is_alive())
            self.assertEqual(state["clicks"], 1)
            self.assertEqual(state["used_aliases"], ["a1_primary"])
            self.assertEqual(len(state["native_executions"]), 1)
        finally:
            release.set()
            if worker.thread is not None:
                worker.thread.join(1)


if __name__ == "__main__":
    unittest.main()
