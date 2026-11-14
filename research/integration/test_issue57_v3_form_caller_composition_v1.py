"""Join the current form grounding contract to the v3 caller and ledger.

All observations, input and saved-form bytes in this test are synthetic. The
test exercises the actual compiled GUI core and public v3 caller result shape;
it is not live GUI or MAP01 evidence.
"""
import hashlib
import json
import tempfile
import time
import unittest
from pathlib import Path

from research.live_control.compiled_form_grounding_v1 import validate
from research.live_control.integrated_efficiency_compiled_adapter_v2 import (
    EXPECTED_METHOD_CONTRACT, compile_form_method,
)
from research.live_control.integrated_efficiency_compiled_execution_v2 import (
    run_compiled_interface_in_caller,
)
from research.live_control.issue57_v3_attempt_ledger_v1 import (
    AppendOnlyAttemptLedger, make_row,
)


def point(x, y):
    return {"point_space": "source_observation_pixels", "point": {"x": x, "y": y},
            "motion_model": "surface_origin_translation"}


GROUNDING = validate({
    "format": "compiled-form-grounding-v1",
    "field": point(100, 200), "submit": point(500, 300),
    "method": {
        "first_action": "enter_exact_token",
        "continue_when": "field_pixels_changed_and_submit_revalidated",
        "second_action": "activate_submit",
        "complete_when": "submission_pixels_changed_then_independent_score",
    },
})


class FormCallerCompositionTests(unittest.TestCase):
    def cell(self, case, root):
        phase = [0]
        sequence = [0]
        inputs = []
        admissions = []
        selected_targets = []
        model_target = {
            "id": "reacquired", "field": "field@100,200-new",
            "submit": "submit@500,300-new", "grounding": GROUNDING,
            "source_sequence": 10,
        }
        cached_target = {
            "id": "cached", "field": "field@100,200-old",
            "submit": "submit@500,300-old", "grounding": GROUNDING,
            "source_sequence": 1,
        }
        source = root / (case + "-source-frame.bin")
        source.write_bytes(("synthetic source frame: " + case).encode())
        saved = root / (case + "-saved-form.json")
        saved_bytes = b'{"value":"exact-token"}\n'

        def interface_for_target(payload):
            target = payload["target"]
            selected_targets.append(target)
            # The actual form validator's source-space points remain attached
            # to the handle references that the caller selected/reacquired.
            self.assertEqual(target["grounding"], GROUNDING)
            return compile_form_method(
                interface_id="synthetic-private-form-v1",
                session_scope="synthetic-session-" + case,
                surface="synthetic-private-form",
                field_handle=target["field"], submit_handle=target["submit"],
                method_contract=EXPECTED_METHOD_CONTRACT,
            )

        def observe(_payload):
            sequence[0] += 1
            current = phase[0]
            return {
                "sequence": sequence[0], "captured_ns": time.perf_counter_ns(),
                "surface": "synthetic-private-form",
                "predicates": {
                    "field_pixels_changed": current >= 1,
                    "field_value_matches_task": current >= 1,
                    "field_target_present": True, "submit_target_present": True,
                    "submission_pixels_changed": current >= 2,
                },
                "evidence_ref": f"synthetic-frame-{sequence[0]}",
                "evidence_digest": f"synthetic-digest-{sequence[0]}",
            }

        def admit(payload):
            reference = payload["symbol"]["target_reference"]
            admissions.append(reference)
            if case == "stale_refusal" and reference.endswith("-old"):
                return {"eligible": False, "status": "stale", "authorization": None,
                        "expected_sequence": payload["observation"]["sequence"],
                        "valid_until_ns": time.perf_counter_ns() + 1_000_000_000}
            return {"eligible": True, "status": "revalidated",
                    "authorization": "synthetic-one-use", "expected_sequence":
                    payload["observation"]["sequence"],
                    "valid_until_ns": time.perf_counter_ns() + 1_000_000_000}

        def execute(payload):
            inputs.append(payload["operation"])
            if case == "release_unknown":
                phase[0] += 1
                return {"status": "completed", "action_id": "synthetic-held-input",
                        "effect_ref": "synthetic-effect", "input_dispatched": True,
                        "release": {"verified": False, "keys_down": ["SHIFT"],
                                    "buttons_down": []}}
            phase[0] += 1
            return {"status": "completed", "action_id": f"synthetic-{phase[0]}",
                    "effect_ref": f"synthetic-effect-{phase[0]}",
                    "input_dispatched": True,
                    "release": {"verified": True, "keys_down": [], "buttons_down": []}}

        def core_verify(payload):
            return {"status": "succeeded",
                    "evidence_ref": payload["observation"]["evidence_ref"]}

        def model_reacquire(_payload):
            return {"call_id": "synthetic-repair-call", "thread_id": "synthetic-thread",
                    "output": {"status": "target_reference", "target": model_target},
                    "usage": {"input_tokens": 31, "output_tokens": 7},
                    "requested_model": "synthetic-model", "requested_effort": "low",
                    "cost": None, "visible_images_submitted": 1, "wait_ns": 1234}

        def post_model_observe(_payload):
            return {"exact": True, "sequence": 11, "capture_ns": 456789,
                    "pointer_binding": {"surface": "synthetic-private-form",
                                        "generation": "new"}}

        def post_model_revalidate(payload):
            current = payload["current_observation"]
            call_id = payload["model_call_id"]
            receipt = {"schema": "post-model-target-revalidation-v1",
                "status": "CURRENT_PATCH_MATCH_NO_AUTHORITY", "model_call_id": call_id,
                "model_source_sequence": 10, "current_sequence": current["sequence"],
                "current_capture_ns": current["capture_ns"],
                "pointer_binding": current["pointer_binding"],
                "grants_semantic_authority": False, "grants_input_authority": False}
            return {"status": "current_patch_match", "target": model_target,
                    "receipt": receipt, "model_call_id": call_id,
                    "grants_semantic_authority": False,
                    "grants_input_authority": False}

        def outer_effect(_payload):
            if case == "effect_unknown":
                return {"status": "unavailable"}
            saved.write_bytes(saved_bytes)
            return {"status": "succeeded", "evidence_ref": "synthetic-saved-form",
                    "evidence_digest": hashlib.sha256(saved_bytes).hexdigest()}

        spec = {"target": "synthetic form", "route": "reuse",
            "coarse_origin": "caller_provided", "provided_coarse": None,
            "cached_target": cached_target, "local_repair_on": [],
            "repair_on": ["stale"] if case == "bounded_repair" else [],
            "session_id": "synthetic-session-" + case}
        caller = {"reuse_revalidate": lambda _: {
                "status": "stale" if case == "bounded_repair" else "revalidated"},
            "final_revalidate": lambda _: {"status": "revalidated"},
            "verify_effect": outer_effect}
        if case == "bounded_repair":
            caller.update(acquire_expansion=lambda _: {"expansion": "bounded"},
                expanded_model=model_reacquire,
                post_model_observe=post_model_observe,
                post_model_revalidate=post_model_revalidate)
        result = run_compiled_interface_in_caller(
            spec, caller, interface_for_target,
            {"observe": observe, "admit": admit, "execute": execute,
             "verify_effect": core_verify, "cancelled": lambda: False},
            id_factory=iter(["attempt-repair-1"]).__next__,
        )
        self.assertTrue(selected_targets)
        self.assertEqual(result["compiled_execution_receipt"]["interface_id"],
                         "synthetic-private-form-v1")
        return result, inputs, admissions, source, saved, model_target

    def test_form_reuse_stale_repair_release_and_effect_all_reach_ledger(self):
        cases = ["reuse", "stale_refusal", "bounded_repair", "release_unknown",
                 "effect_unknown"]
        with tempfile.TemporaryDirectory(prefix="issue57-form-caller-") as td:
            root = Path(td)
            assignments = ["form-" + case for case in cases]
            ledger = AppendOnlyAttemptLedger(root / "attempts.jsonl", assignments)
            observed = {}
            for case in cases:
                with self.subTest(case=case):
                    result, inputs, admissions, source, saved, repaired = self.cell(case, root)
                    receipt = result["compiled_execution_receipt"]
                    terminals = [event for event in receipt["critical_events"]
                                 if event.get("event") == "action_terminal"]
                    all_released = bool(terminals) and all(
                        event.get("release_verified") is True for event in terminals)
                    if all_released:
                        receipt_digest = hashlib.sha256((json.dumps(receipt, sort_keys=True,
                            separators=(",", ":"), ensure_ascii=False) + "\n").encode()).hexdigest()
                        release = {"status": "succeeded", "verified": True,
                            "keys_down": [], "buttons_down": [],
                            "evidence_ref": "compiled-runtime-receipt",
                            "evidence_digest": receipt_digest}
                    else:
                        release = {"status": "unavailable", "verified": None,
                            "keys_down": None, "buttons_down": None,
                            "evidence_ref": None, "evidence_digest": None}
                    effect = result.get("effect_receipt") or {
                        "status": "unavailable", "evidence_ref": None,
                        "evidence_digest": None}
                    raw = [source] + ([saved] if saved.exists() else [])
                    row = make_row("form-" + case, result, release, effect, raw_paths=raw)
                    ledger.append(row)
                    observed[case] = (result, inputs, admissions, release, effect, row,
                                      source, saved)

            audit = ledger.audit()
            self.assertEqual(audit["assignment_ids"], assignments)
            self.assertEqual(observed["reuse"][0]["outcome"], "TASK_SUCCEEDED")
            self.assertEqual(observed["reuse"][1], ["enter_exact_token", "activate_submit"])
            self.assertEqual(observed["reuse"][0]["repair_path"], "none")
            self.assertEqual(observed["reuse"][0]["attempt_ledger"], [])
            self.assertEqual(observed["stale_refusal"][0]["outcome"], "EXECUTION_INCOMPLETE")
            self.assertEqual(observed["stale_refusal"][1], [])
            self.assertEqual(observed["stale_refusal"][2][0], "field@100,200-old")
            self.assertEqual(observed["stale_refusal"][3]["status"], "unavailable")
            repaired_result = observed["bounded_repair"][0]
            self.assertEqual(repaired_result["repair_path"], "model_reacquisition")
            self.assertEqual(repaired_result["repair_trace"][-1],
                {"stage": "post_model_revalidate", "status": "current_patch_match"})
            self.assertEqual(repaired_result["attempt_ledger"][0]["usage"],
                             {"input_tokens": 31, "output_tokens": 7})
            self.assertEqual(observed["bounded_repair"][0]["selected_target"], repaired)
            self.assertEqual(observed["release_unknown"][0]["outcome"], "EXECUTION_INCOMPLETE")
            self.assertIsNone(observed["release_unknown"][0]["task_effect"])
            self.assertEqual(observed["release_unknown"][3]["status"], "unavailable")
            self.assertFalse(next(event for event in
                observed["release_unknown"][0]["compiled_execution_receipt"]["critical_events"]
                if event.get("event") == "action_terminal")["release_verified"])
            self.assertEqual(observed["effect_unknown"][0]["outcome"], "TASK_NOT_VERIFIED")
            self.assertEqual(observed["effect_unknown"][0]["task_effect"], "unavailable")
            self.assertEqual(observed["effect_unknown"][3]["status"], "succeeded")
            self.assertEqual(observed["effect_unknown"][4]["status"], "unavailable")
            for case in cases:
                row = observed[case][5]
                source = observed[case][6]
                self.assertEqual(row["raw_evidence"][0]["sha256"],
                                 hashlib.sha256(source.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
