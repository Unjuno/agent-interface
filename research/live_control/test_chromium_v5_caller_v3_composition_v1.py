"""Fake-only composition of V5 point mints, caller v3, and compiled GUI."""
import copy
import hashlib
import time
import unittest

from PIL import Image

from model_point_target_v1 import OPERATION
from research.live_control.test_chromium_v5_generation_mint_guard_v1 import (
    GEN_A, GEN_B, Harness, PointMintBackend, textured_image,
)
from research.live_control.integrated_efficiency_compiled_adapter_v2 import (
    EXPECTED_METHOD_CONTRACT, compile_form_method,
)
from research.live_control.integrated_efficiency_compiled_execution_v2 import (
    run_compiled_interface_in_caller,
)
from runtime.guarded_x11_v1.handles import TargetHandleStore


SCOPE = "chromium-v5-composition-fake-scope"
SURFACE = "chromium-v5-composition-surface"


def _point_mint(harness, alias, point):
    step = {
        "op": OPERATION,
        "name": alias,
        "coordinate_frame": "window_content",
        "source_sequence": 1,
        "point": point,
        "region_size": [16, 16],
        "ttl_ms": 30_000,
        "freshness_ms": 1_000,
        "search_radius": 0,
        "allowed_transformations": ["window_translation"],
    }
    return PointMintBackend.execute(harness, step, None, "mint-" + alias, 0)


def _resolution(harness, alias, offset, sequence, generation):
    captured = time.perf_counter_ns()
    observation = {
        "sequence": sequence,
        "capture_ns": captured,
        "pointer_binding": {
            "focus": 17,
            "surface": 29,
            "geometry": [0, 0, 160, 120],
            "process_generation": GEN_A,
            "window_generation": generation,
        },
    }
    result = harness.handles.resolve_point(
        alias, offset, observation, harness.image(), time.perf_counter_ns(),
        session_scope=SCOPE,
    )
    return result, observation


class ChromiumV5CallerV3CompositionTests(unittest.TestCase):
    def _run(self, *, change_generation_after_entry=False):
        harness = Harness(GEN_A, GEN_A)
        ids = iter(("private-field-id", "private-submit-id"))
        harness.handles = TargetHandleStore(SCOPE, id_factory=lambda: next(ids))
        harness.current["pointer_binding"]["window_generation"] = GEN_A
        harness.point_source_history[1]["observation"]["pointer_binding"][
            "window_generation"] = GEN_A
        field = _point_mint(harness, "field", [40, 40])
        submit = _point_mint(harness, "submit", [80, 40])
        self.assertEqual(field["source_patch_sha256"], field["fresh_patch_sha256"])
        self.assertEqual(submit["source_patch_sha256"], submit["fresh_patch_sha256"])
        self.assertIs(field["private_registry_id_exposed"], False)
        self.assertIs(submit["private_registry_id_exposed"], False)
        self.assertEqual(set(harness.handles._entries),
                         {"private-field-id", "private-submit-id"})

        handles = {
            field["handle"]: {"offset": field["derived_offset"]},
            submit["handle"]: {"offset": submit["derived_offset"]},
        }
        state = {
            "generation": GEN_A,
            "sequence": harness.sequence,
            "executed": [],
            "admissions": [],
            "core_effect_checks": [],
            "outer_effect_checks": [],
            "journal": [],
            "generation_changed": False,
        }

        def current_resolution(alias, offset):
            state["sequence"] += 1
            return _resolution(harness, alias, offset, state["sequence"],
                               state["generation"])[0]

        def reuse_revalidate(target):
            for alias in target.values():
                resolution = current_resolution(alias, handles[alias]["offset"])
                if not resolution["eligible"]:
                    return {"status": "association_changed"}
            return {"status": "revalidated"}

        def final_revalidate(payload):
            target = payload
            for alias in target.values():
                resolution = current_resolution(alias, handles[alias]["offset"])
                if not resolution["eligible"]:
                    return {"status": "association_changed"}
            return {"status": "revalidated"}

        def interface_for_target(payload):
            target = payload["target"]
            return compile_form_method(
                interface_id="chromium-v5-caller-v3-form",
                session_scope=SCOPE,
                surface=SURFACE,
                field_handle=target["field"],
                submit_handle=target["submit"],
                method_contract=EXPECTED_METHOD_CONTRACT,
            )

        def observe(_payload):
            state["sequence"] += 1
            count = len(state["executed"])
            capture_ns = time.perf_counter_ns()
            observation = {
                "sequence": state["sequence"],
                "captured_ns": capture_ns,
                "surface": SURFACE,
                "predicates": {
                    "field_pixels_changed": count >= 1,
                    "field_value_matches_task": count >= 1,
                    "field_target_present": True,
                    "submit_target_present": True,
                    "submission_pixels_changed": count >= 2,
                },
                "evidence_ref": "fake-chromium-frame-" + str(state["sequence"]),
                "evidence_digest": hashlib.sha256(
                    (str(state["sequence"]) + state["generation"]).encode()
                ).hexdigest(),
            }
            state["last_observation"] = observation
            return observation

        def admit(payload):
            symbol = payload["symbol"]
            alias = symbol["target_reference"]
            resolved = harness.handles.resolve_point(
                alias,
                handles[alias]["offset"],
                {
                    "sequence": payload["observation"]["sequence"],
                    "capture_ns": payload["observation"]["captured_ns"],
                    "pointer_binding": {
                        "focus": 17,
                        "surface": 29,
                        "geometry": [0, 0, 160, 120],
                        "process_generation": GEN_A,
                        "window_generation": state["generation"],
                    },
                },
                harness.image(),
                time.perf_counter_ns(),
                session_scope=SCOPE,
            )
            state["admissions"].append({"alias": alias,
                                        "resolution": copy.deepcopy(resolved)})
            if not resolved["eligible"]:
                mapping = {"STALE": "stale", "MISSING": "missing",
                           "SCOPE_MISMATCH": "association_changed",
                           "AMBIGUOUS": "missing", "MOVED": "stale"}
                return {"eligible": False,
                        "status": mapping.get(resolved["status"], "association_changed"),
                        "authorization": None,
                        "expected_sequence": payload["observation"]["sequence"],
                        "valid_until_ns": time.perf_counter_ns() + 1_000_000_000}
            return {"eligible": True, "status": "revalidated",
                    "authorization": "fake-only-admission-token",
                    "expected_sequence": payload["observation"]["sequence"],
                    "valid_until_ns": min(resolved["valid_until_ns"],
                                           time.perf_counter_ns() + 500_000_000)}

        def execute(payload):
            state["executed"].append(copy.deepcopy(payload))
            row = {"status": "completed", "action_id": "action-" + str(len(state["executed"])),
                   "effect_ref": "fake-effect-" + str(len(state["executed"])),
                   "release": {"verified": True, "keys_down": [], "buttons_down": []},
                   "input_dispatched": True}
            if change_generation_after_entry and len(state["executed"]) == 1:
                state["generation"] = GEN_B
                state["generation_changed"] = True
            return row

        def verify_core_effect(payload):
            state["core_effect_checks"].append(copy.deepcopy(payload))
            return {"status": "succeeded",
                    "evidence_ref": "fake-core-effect-" + str(len(state["core_effect_checks"]))}

        def verify_outer_effect(payload):
            state["outer_effect_checks"].append(copy.deepcopy(payload))
            receipt = state.get("compiled_receipt")
            if receipt is None or receipt["completed_transitions"] != 2:
                return {"status": "unavailable", "evidence_ref": "outer-incomplete"}
            return {"status": "succeeded", "evidence_ref": "outer-score-two-actions"}

        def retain(receipt):
            state["compiled_receipt"] = copy.deepcopy(receipt)

        def journal(event):
            state["journal"].append(copy.deepcopy(event))

        target = {"field": field["handle"], "submit": submit["handle"]}
        spec = {
            "target": "Chromium form with exact task token",
            "route": "reuse",
            "coarse_origin": "caller_provided",
            "provided_coarse": None,
            "cached_target": copy.deepcopy(target),
            "local_repair_on": [],
            "repair_on": [],
            "session_id": SCOPE,
        }
        caller_adapters = {
            "reuse_revalidate": reuse_revalidate,
            "final_revalidate": final_revalidate,
            "verify_effect": verify_outer_effect,
            "journal": journal,
        }
        result = run_compiled_interface_in_caller(
            spec,
            caller_adapters,
            interface_for_target,
            {"observe": observe, "admit": admit, "execute": execute,
             "verify_effect": verify_core_effect, "cancelled": lambda: False},
            on_receipt=retain,
        )
        state["outer_outcome"] = result["outcome"]
        return result, state, field, submit

    def test_v5_point_handles_flow_through_caller_v3_and_compiled_task_score(self):
        result, state, field, submit = self._run()
        self.assertEqual(result["outcome"], "TASK_SUCCEEDED", result)
        self.assertEqual(result["task_effect"], "succeeded")
        self.assertEqual(result["selected_target"],
                         {"field": field["handle"], "submit": submit["handle"]})
        self.assertEqual(len(state["executed"]), 2)
        self.assertEqual([row["operation"] for row in state["executed"]],
                         ["enter_exact_token", "activate_submit"])
        self.assertEqual(len(state["admissions"]), 2)
        self.assertTrue(all(row["resolution"]["eligible"] for row in state["admissions"]))
        self.assertEqual(len(state["core_effect_checks"]), 2)
        self.assertEqual(len(state["outer_effect_checks"]), 1)
        self.assertEqual(result["compiled_execution_receipt"]["completed_transitions"], 2)
        self.assertTrue(all(row["release_verified"]
                            for row in result["compiled_execution_receipt"]["transitions"]))
        self.assertIs(state["generation_changed"], False)

    def test_generation_change_after_entry_refuses_submit_and_keeps_partial_release(self):
        result, state, _field, _submit = self._run(change_generation_after_entry=True)
        self.assertEqual(result["outcome"], "EXECUTION_INCOMPLETE", result)
        self.assertEqual(result["delivery"], "confirmed_partial")
        self.assertEqual(result["execution_progress"]["completed_actions"], 1)
        self.assertEqual(len(state["executed"]), 1)
        self.assertEqual(state["executed"][0]["operation"], "enter_exact_token")
        self.assertEqual(len(state["admissions"]), 2)
        self.assertTrue(state["admissions"][0]["resolution"]["eligible"])
        self.assertEqual(state["admissions"][1]["resolution"]["status"],
                         "SCOPE_MISMATCH")
        self.assertEqual(state["admissions"][1]["resolution"]["reason"],
                         "window_generation_changed_or_missing")
        self.assertEqual(len(state["core_effect_checks"]), 1)
        self.assertEqual(len(state["outer_effect_checks"]), 0)
        receipt = result["compiled_execution_receipt"]
        self.assertEqual(receipt["completed_transitions"], 1)
        self.assertIs(receipt["transitions"][0]["release_verified"], True)
        self.assertEqual(receipt["reason"], "association_changed")
        self.assertIs(state["generation_changed"], True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
