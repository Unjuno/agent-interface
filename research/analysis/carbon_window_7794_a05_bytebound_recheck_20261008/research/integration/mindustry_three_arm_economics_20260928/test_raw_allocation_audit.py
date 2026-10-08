"""Synthetic corruption controls for independent raw Mindustry audit."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from raw_allocation_audit_v1 import audit, audit_file, reconstruct  # noqa: E402


ARMS = ("plain", "ephemeral", "persistent")
TASKS = ("A1", "A2", "A3", "B1", "B2", "B3")
LAYOUTS = ("A", "A", "A", "B", "B", "B")
ROUTES = {
    "plain": ("cold",) * 6,
    "ephemeral": ("cold",) * 6,
    "persistent": ("cold", "reuse", "reuse", "repair", "reuse", "reuse"),
}
COUNTS = {"plain": (1,) * 6, "ephemeral": (1,) * 6,
          "persistent": (1, 0, 0, 1, 0, 0)}
MODEL = "gpt-5.6-luna"
EFFORT = "low"
USAGE_ZERO = {"input_tokens": 0, "cached_input_tokens": 0,
              "cache_write_input_tokens": 0, "output_tokens": 0,
              "reasoning_output_tokens": 0}
SCORE_SCOPE = "one changed-geometry Mindustry placement; no delivery or route-completion claim"


def source_identity():
    digest = "a" * 64
    return {"commit": "0" * 40, "preregistration_sha256": digest,
            "runner_sha256": digest, "raw_auditor_sha256": digest,
            "decision_evaluator_sha256": digest, "mod_sha256": digest,
            "jar_sha256": digest, "save_sha256": digest,
            "container_image_digest": "sha256:" + "b" * 64}


def score(at_ns):
    return {"status": "VERIFIED", "contract_satisfied": True,
            "wrong_target": False, "collateral_tiles": [],
            "source_preserved": True, "core_preserved": True,
            "copper_delta": -1, "paused_idle_completion": True,
            "guard_tiles": 112, "scope": SCORE_SCOPE, "checked_ns": at_ns}


def raw_allocation():
    preflight = []
    arms = {arm: [] for arm in ARMS}
    for arm in ARMS:
        preflight.append({"arm": arm, "call_id": f"preflight-{arm}",
            "stage": "schema_preflight", "requested_model": MODEL,
            "requested_effort": EFFORT, "usage": {**USAGE_ZERO, "input_tokens": 8_000},
            "image_count": 0})
        for index, task_id in enumerate(TASKS):
            start = 1_000_000_000 * (1 + ARMS.index(arm) * 6 + index)
            end = start + 20_000
            source_seq = index * 3 + 1
            frame = hashlib.sha256(f"{arm}/{task_id}/frame".encode()).hexdigest()
            calls = []
            count = COUNTS[arm][index]
            if count:
                calls.append({"call_id": f"{arm}-{task_id}-call-1",
                    "stage": "repair" if ROUTES[arm][index] == "repair" else "grounding",
                    "requested_model": MODEL, "requested_effort": EFFORT,
                    "usage": {**USAGE_ZERO, "input_tokens": 9_000, "output_tokens": 100},
                    "source_sequence": source_seq, "image_sha256": frame})
            observations = [
                {"sequence": source_seq, "capture_ns": start + 100,
                 "image_sha256": frame, "model_visible": bool(count)},
                {"sequence": source_seq + 1, "capture_ns": start + 200,
                 "image_sha256": hashlib.sha256(f"{arm}/{task_id}/local".encode()).hexdigest(),
                 "model_visible": False},
            ]
            inputs = []
            if arm == "persistent" and index == 3:
                inputs.append({"attempt_id": f"{task_id}-old", "status": "REFUSED",
                    "old_reference": True, "admission_ns": None})
            for action in ("palette", "world"):
                inputs.append({"attempt_id": f"{arm}-{task_id}-{action}",
                    "status": "ADMITTED", "old_reference": False,
                    "admission_ns": start + 1_000 + (0 if action == "palette" else 500)})
            admitted = [event for event in inputs if event["status"] == "ADMITTED"]
            releases = [{"attempt_id": event["attempt_id"],
                "released_ns": event["admission_ns"] + 200,
                "button_up": True, "keys_empty": True,
                "receipt_id": "release-" + event["attempt_id"]} for event in admitted]
            feedback = [{"attempt_id": event["attempt_id"],
                "observed_ns": event["admission_ns"] + 100} for event in admitted]
            repairs = []
            if arm == "persistent" and index == 3:
                repairs.append({"old_reference_status": "association_changed",
                    "old_reference_sequence": 7, "observed_sequence": source_seq,
                    "old_reference_pointer_admitted": False,
                    "fresh_call_id": calls[0]["call_id"],
                    "fresh_source_sequence": source_seq})
            arms[arm].append({"task_id": task_id, "layout": LAYOUTS[index],
                "route": ROUTES[arm][index], "started_ns": start, "ended_ns": end,
                "observation_events": observations, "model_call_events": calls,
                "durable_call_ids": [f"{arm}-{task_id}-tool-{n}" for n in range(5)],
                "input_events": inputs, "input_feedback_events": feedback,
                "release_events": releases,
                "submission_events": [{"submission_id": f"score-{arm}-{task_id}",
                    "at_ns": start + 3_000, "exact_effect": True}],
                "score_event": score(start + 4_000), "repair_events": repairs})
    return {"schema": "mindustry_three_arm_raw_events_v1",
        "allocation_id": "mindustry-three-arm-economics-construction-raw-01",
        "source_identity": source_identity(),
        "model_identity": {"requested_model": MODEL, "requested_effort": EFFORT},
        "preflight_events": preflight, "arms": arms}


class RawAllocationAuditTests(unittest.TestCase):
    def setUp(self):
        self.raw = raw_allocation()

    def test_event_reconstruction_reaches_frozen_positive_disposition(self):
        trace = reconstruct(self.raw)
        self.assertEqual(tuple(trace["arms"]), ARMS)
        self.assertEqual(trace["arms"]["persistent"][3]["repair"]["succeeded"], True)
        result = audit(json.dumps(self.raw, sort_keys=True).encode())
        self.assertEqual(result["audit"], "PASS_CONSTRUCTION_ONLY")
        self.assertFalse(result["source_identity_verified"])
        self.assertEqual(result["evaluation"]["disposition"], "RETAIN")
        self.assertEqual(result["evaluation"]["observed_break_even_task"], 2)

    def test_raw_identity_must_match_separately_supplied_freeze(self):
        expected = source_identity()
        result = audit(json.dumps(self.raw).encode(), expected_source_identity=expected)
        self.assertEqual(result["audit"], "PASS_RAW_RECONSTRUCTION")
        self.assertTrue(result["source_identity_verified"])

    def test_formal_file_entrypoint_reads_raw_and_external_freeze_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw_path, freeze_path = root / "raw.json", root / "freeze.json"
            raw_path.write_text(json.dumps(self.raw), encoding="utf-8")
            freeze_path.write_text(json.dumps({"source_identity": source_identity()}),
                                   encoding="utf-8")
            result = audit_file(raw_path, freeze_path)
        self.assertEqual(result["audit"], "PASS_RAW_RECONSTRUCTION")
        self.assertTrue(result["source_identity_verified"])

    def test_aggregate_summary_fields_are_not_accepted_as_raw_events(self):
        changed = copy.deepcopy(self.raw)
        changed["arms"]["plain"][0]["planner_generations"] = 99
        with self.assertRaisesRegex(ValueError, "aggregates refused"):
            reconstruct(changed)

    def test_wrong_frozen_route_is_rejected(self):
        changed = copy.deepcopy(self.raw)
        changed["arms"]["persistent"][3]["route"] = "reuse"
        with self.assertRaisesRegex(ValueError, "route differs"):
            reconstruct(changed)

    def test_model_call_must_bind_exact_visible_image(self):
        changed = copy.deepcopy(self.raw)
        changed["arms"]["plain"][0]["model_call_events"][0]["image_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "does not bind"):
            reconstruct(changed)

    def test_missing_release_receipt_holds_raw_audit(self):
        changed = copy.deepcopy(self.raw)
        changed["arms"]["plain"][0]["release_events"].pop()
        result = audit(json.dumps(changed).encode())
        self.assertEqual(result["audit"], "HOLD_RAW_RECONSTRUCTION")
        self.assertIn("every admitted input", result["errors"][0])

    def test_old_target_admission_cannot_be_hidden_by_repair_claim(self):
        changed = copy.deepcopy(self.raw)
        task = changed["arms"]["persistent"][3]
        old = task["input_events"][0]
        old["status"], old["admission_ns"] = "ADMITTED", task["started_ns"] + 700
        task["input_feedback_events"].append({"attempt_id": old["attempt_id"],
                                             "observed_ns": old["admission_ns"] + 50})
        task["release_events"].append({"attempt_id": old["attempt_id"],
            "released_ns": old["admission_ns"] + 100, "button_up": True,
            "keys_empty": True, "receipt_id": "release-old-target"})
        result = audit(json.dumps(changed).encode())
        self.assertEqual(result["audit"], "HOLD_RAW_RECONSTRUCTION")
        self.assertIn("B1 repair", result["errors"][0])

    def test_private_score_cannot_override_wrong_raw_effect(self):
        changed = copy.deepcopy(self.raw)
        changed["arms"]["plain"][0]["submission_events"][0]["exact_effect"] = False
        result = audit(json.dumps(changed).encode())
        self.assertEqual(result["audit"], "HOLD_RAW_RECONSTRUCTION")
        self.assertIn("contradicts raw", result["errors"][0])

    def test_raw_usage_can_be_valid_but_economics_gate_can_reject(self):
        changed = copy.deepcopy(self.raw)
        for task in changed["arms"]["persistent"]:
            for call in task["model_call_events"]:
                call["usage"]["input_tokens"] = 30_000
        result = audit(json.dumps(changed).encode(),
                       expected_source_identity=changed["source_identity"])
        self.assertEqual(result["audit"], "PASS_RAW_RECONSTRUCTION")
        self.assertEqual(result["evaluation"]["disposition"], "REJECT")
        self.assertEqual(result["evaluation"]["reason"],
            "frozen_token_generation_or_break_even_gate_failed")

    def test_source_hash_claim_must_match_external_freeze(self):
        changed = copy.deepcopy(self.raw)
        changed["source_identity"]["mod_sha256"] = "c" * 64
        expected = copy.deepcopy(self.raw["source_identity"])
        result = audit(json.dumps(changed).encode(), expected_source_identity=expected)
        self.assertEqual(result["audit"], "HOLD_RAW_RECONSTRUCTION")
        self.assertFalse(result["source_identity_verified"])
        self.assertIn("differs from independent freeze", result["errors"][0])

    def test_source_identity_requires_immutable_image_digest(self):
        changed = copy.deepcopy(self.raw)
        changed["source_identity"]["container_image_digest"] = "latest"
        with self.assertRaisesRegex(ValueError, "immutable container image"):
            reconstruct(changed)


if __name__ == "__main__":
    unittest.main()
