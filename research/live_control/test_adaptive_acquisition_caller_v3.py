"""Branch-complete offline checks for adaptive acquisition caller v3."""
import unittest

from adaptive_acquisition_caller_v3 import ModelFailure, run


TARGET = {"handle": "save-v1", "point": [300, 240]}
REPAIRED = {"handle": "save-v1", "point": [270, 243]}
USAGE = {"input_tokens": 9351, "cached_input_tokens": 0,
         "cache_write_input_tokens": 0, "output_tokens": 100,
         "reasoning_output_tokens": 50}


class Clock:
    def __init__(self): self.value = 1000
    def __call__(self):
        self.value += 10
        return self.value


def spec(*, local_on=None, model_on=None):
    return {"target": "Save", "route": "reuse",
            "coarse_origin": "caller_provided", "provided_coarse": None,
            "cached_target": TARGET,
            "local_repair_on": local_on or [], "repair_on": model_on or [],
            "session_id": "offline-v3"}


def model_result(output=None, call_id="model-1"):
    return {"call_id": call_id,
            "output": output or {"status": "target_reference", "target": REPAIRED},
            "usage": USAGE, "requested_model": "gpt-5.6-luna",
            "requested_effort": "low", "cost": None,
            "visible_images_submitted": 1, "wait_ns": 8_100_000_000}


def current_receipt(call_id="model-1"):
    return {"schema": "post-model-target-revalidation-v1",
            "status": "CURRENT_PATCH_MATCH_NO_AUTHORITY",
            "model_call_id": call_id, "model_source_sequence": 4,
            "current_sequence": 5, "current_capture_ns": 500,
            "pointer_binding": {"focus": 2, "surface": 3,
                                "geometry": [0, 0, 800, 600]},
            "grants_semantic_authority": False,
            "grants_input_authority": False}


def adapters(*, reuse="association_changed", local=None, post="match",
             model=None, calls=None, execute=None):
    calls = calls if calls is not None else []

    def value(name, result):
        def invoke(payload):
            calls.append(name)
            return result(payload) if callable(result) else result
        return invoke

    local_result = local or {"status": "repaired", "target": REPAIRED,
        "receipt": {"schema": "target-handle-semantic-repair-v1"},
        "model_calls": 0, "grants_semantic_authority": False,
        "grants_input_authority": False}
    if post == "match":
        post_result = {"status": "current_patch_match", "target": REPAIRED,
            "receipt": current_receipt(), "model_call_id": "model-1",
            "grants_semantic_authority": False,
            "grants_input_authority": False}
    else:
        post_result = {"status": post}
    return {
        "reuse_revalidate": value("reuse_revalidate", {"status": reuse}),
        "local_repair": value("local_repair", local_result),
        "acquire_expansion": value("acquire_expansion", {"image": "current"}),
        "expanded_model": value("expanded_model", model or model_result()),
        "post_model_observe": value("post_model_observe", {"sequence": 5,
            "capture_ns": 500, "exact": True,
            "pointer_binding": {"focus": 2, "surface": 3,
                                "geometry": [0, 0, 800, 600]}}),
        "post_model_revalidate": value("post_model_revalidate", post_result),
        "final_revalidate": value("final_revalidate", {"status": "revalidated"}),
        "execute": value("execute", execute or {"status": "completed"}),
        "verify_effect": value("verify_effect", {"status": "succeeded"})}


class CallerV3Test(unittest.TestCase):
    def run_case(self, specification, mapping, ids=()):
        return run(specification, mapping, clock=Clock(),
                   id_factory=iter(ids).__next__ if ids else None)

    def test_unchanged_reuse_uses_no_repair(self):
        calls = []
        result = self.run_case(spec(), adapters(reuse="revalidated", calls=calls))
        self.assertEqual(result["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(result["repair_path"], "none")
        self.assertEqual(result["accounting"]["attempted_calls"], 0)
        self.assertNotIn("local_repair", calls)

    def test_cold_anchor_path_preserves_full_accounting(self):
        cold = {"target": "Save", "route": "cold",
            "coarse_origin": "model_produced", "provided_coarse": None,
            "cached_target": None, "local_repair_on": [], "repair_on": [],
            "session_id": "offline-v3-cold"}
        mapping = {
            "observe_source": lambda payload: {"image": "source"},
            "coarse_model": lambda payload: model_result(
                {"status": "candidate", "point": [300, 240]}, "cold-1"),
            "acquire_anchor": lambda payload: {"image": "anchor"},
            "anchor_model": lambda payload: model_result(
                {"status": "target_reference", "target": TARGET}, "cold-2"),
            "final_revalidate": lambda payload: {"status": "revalidated"},
            "execute": lambda payload: {"status": "completed"},
            "verify_effect": lambda payload: {"status": "succeeded"}}
        result = self.run_case(cold, mapping, ids=["cold-a", "cold-b"])
        self.assertEqual(result["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(result["comparison"]["class"], "full_cold")
        self.assertEqual(result["accounting"]["attempted_calls"], 2)
        self.assertEqual(result["accounting"]["usage_totals"]["input_tokens"], 18_702)
        self.assertEqual(result["accounting"]["visible_images_submitted"], 2)
        self.assertEqual(result["accounting"]["model_wait_ns"], 16_200_000_000)

    def test_local_repair_precedes_model_and_uses_zero_calls(self):
        calls = []
        result = self.run_case(spec(local_on=["association_changed"],
                                    model_on=["missing", "ambiguous", "association_changed"]),
                               adapters(calls=calls))
        self.assertEqual(result["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(result["repair_path"], "local")
        self.assertEqual(result["repair_trace"], [
            {"stage": "reuse_revalidate", "status": "association_changed"},
            {"stage": "local_repair", "status": "repaired"}])
        self.assertEqual(result["selected_target"], REPAIRED)
        self.assertEqual(result["accounting"]["attempted_calls"], 0)
        self.assertNotIn("expanded_model", calls)

    def test_final_revalidation_promotes_refreshed_cache_atomically(self):
        refreshed = {"handle": "save-current", "point": [271, 243]}
        mapping = adapters(reuse="revalidated")
        mapping["final_revalidate"] = lambda payload: {
            "status": "revalidated", "target": refreshed}
        observed = []
        mapping["execute"] = lambda payload: (
            observed.append(payload["target"]) or {"status": "completed"})
        result = self.run_case(spec(), mapping)
        self.assertEqual(result["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(result["selected_target"], refreshed)
        self.assertEqual(result["cache_update"], refreshed)
        self.assertEqual(observed, [refreshed])

    def test_missing_ambiguous_and_changed_fall_back_once(self):
        for fallback in ("missing", "ambiguous", "association_changed"):
            with self.subTest(fallback=fallback):
                calls = []
                result = self.run_case(
                    spec(local_on=["association_changed"],
                         model_on=["missing", "ambiguous", "association_changed"]),
                    adapters(local={"status": fallback}, calls=calls), ids=[fallback])
                self.assertEqual(result["outcome"], "TASK_SUCCEEDED")
                self.assertEqual(result["repair_path"], "model_reacquisition")
                self.assertEqual(result["repair_trace"], [
                    {"stage": "reuse_revalidate", "status": "association_changed"},
                    {"stage": "local_repair", "status": fallback},
                    {"stage": "model_reacquisition", "status": "target_reference"},
                    {"stage": "post_model_revalidate", "status": "current_patch_match"}])
                self.assertEqual(result["accounting"]["attempted_calls"], 1)
                self.assertEqual(result["accounting"]["completed_calls"], 1)
                self.assertEqual(result["accounting"]["usage_totals"], USAGE)
                self.assertEqual(result["accounting"]["visible_images_submitted"], 1)
                self.assertEqual(result["accounting"]["model_wait_ns"], 8_100_000_000)
                self.assertLess(calls.index("local_repair"), calls.index("expanded_model"))
                self.assertLess(calls.index("expanded_model"), calls.index("post_model_observe"))
                self.assertLess(calls.index("post_model_revalidate"), calls.index("execute"))

    def test_unconfigured_failure_stops_without_model_or_input(self):
        calls = []
        result = self.run_case(spec(local_on=["association_changed"], model_on=["missing"]),
                               adapters(local={"status": "ambiguous"}, calls=calls))
        self.assertEqual((result["outcome"], result["reason"]),
                         ("SAFE_STOP", "ambiguous"))
        self.assertNotIn("expanded_model", calls)
        self.assertNotIn("execute", calls)
        self.assertEqual(result["input_authority"], "none")

    def test_post_model_changed_evidence_stops_before_input(self):
        calls = []
        result = self.run_case(
            spec(local_on=["association_changed"], model_on=["missing"]),
            adapters(local={"status": "missing"}, post="association_changed", calls=calls),
            ids=["changed"])
        self.assertEqual((result["outcome"], result["reason"]),
                         ("SAFE_STOP", "association_changed"))
        self.assertNotIn("execute", calls)
        self.assertEqual(result["accounting"]["attempted_calls"], 1)

    def test_stale_same_frame_receipt_fails_closed(self):
        calls = []
        bad = {"status": "current_patch_match", "target": REPAIRED,
            "receipt": {**current_receipt(), "current_sequence": 4},
            "model_call_id": "model-1", "grants_semantic_authority": False,
            "grants_input_authority": False}
        mapping = adapters(local={"status": "missing"}, calls=calls)
        mapping["post_model_revalidate"] = lambda payload: bad
        result = self.run_case(spec(local_on=["association_changed"], model_on=["missing"]),
                               mapping, ids=["stale"])
        self.assertEqual(result["outcome"], "CALLER_FAILED")
        self.assertIn("exact current no-authority", result["reason"])
        self.assertNotIn("execute", calls)

    def test_local_repair_cannot_claim_authority(self):
        bad = {"status": "repaired", "target": REPAIRED,
            "receipt": {}, "model_calls": 0,
            "grants_semantic_authority": True, "grants_input_authority": False}
        result = self.run_case(spec(local_on=["association_changed"]), adapters(local=bad))
        self.assertEqual(result["outcome"], "CALLER_FAILED")
        self.assertEqual(result["accounting"]["attempted_calls"], 0)

    def test_failed_model_attempt_retains_available_accounting(self):
        def fail(payload):
            raise ModelFailure("upstream", call_id="failed-1", usage=USAGE,
                               visible_images_submitted=1, wait_ns=2_000_000)
        result = self.run_case(
            spec(local_on=["association_changed"], model_on=["missing"]),
            adapters(local={"status": "missing"}, model=fail), ids=["attempt-1"])
        self.assertEqual(result["outcome"], "CALLER_FAILED")
        self.assertEqual(result["accounting"]["attempted_calls"], 1)
        self.assertEqual(result["accounting"]["completed_calls"], 0)
        self.assertEqual(result["accounting"]["usage_totals"], USAGE)
        self.assertEqual(result["accounting"]["visible_images_submitted"], 1)
        self.assertEqual(result["accounting"]["model_wait_ns"], 2_000_000)

    def test_capacity_deferral_is_not_generic_failure(self):
        def defer(payload):
            raise ModelFailure("capacity", visible_images_submitted=1,
                               wait_ns=3_000_000,
                               typed_status="DEFERRED_UPSTREAM")
        result = self.run_case(
            spec(local_on=["association_changed"], model_on=["missing"]),
            adapters(local={"status": "missing"}, model=defer),
            ids=["deferred-attempt"])
        self.assertEqual((result["outcome"], result["reason"]),
                         ("TASK_DEFERRED", "deferred_upstream"))
        self.assertEqual(result["accounting"]["attempted_calls"], 1)
        self.assertEqual(result["accounting"]["completed_calls"], 0)
        self.assertEqual(result["accounting"]["visible_images_submitted"], 1)
        self.assertEqual(result["input_authority"], "none")

    def test_partial_execution_reason_survives(self):
        result = self.run_case(spec(), adapters(
            reuse="revalidated", execute={"status": "safe_yield",
            "reason": "unknown_state", "completed_actions": 1}))
        self.assertEqual(result["outcome"], "EXECUTION_INCOMPLETE")
        self.assertEqual(result["reason"], "unknown_state")
        self.assertEqual(result["delivery"], "confirmed_partial")


if __name__ == "__main__":
    unittest.main()
