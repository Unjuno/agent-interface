"""Mutation tests for the independent raw-output auditor; no model is loaded."""
from __future__ import annotations

import copy
import hashlib
import json
import unittest
from collections import defaultdict

from audit_results import audit, reference_bind, reference_effect
from make_dataset import build
from sampler import CLASSES, select_support


FORMAL_SEED = 73194111
SUPPORT_SEED = 51829177
ALLOCATION = "qwen5139-construction-only-fixture"


def fixture():
    data = build(FORMAL_SEED, SUPPORT_SEED, ALLOCATION)
    raw_bytes = (json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n").encode()
    digest = hashlib.sha256(raw_bytes).hexdigest()
    documents = {}
    for arm in ("base", "imbalanced", "balanced"):
        results = []
        for row in data["heldout"]:
            intent = row["intent"]
            bound = reference_bind(intent, row["state"], row["requested_generation"])
            effect = reference_effect(bound, row["state"])
            raw_text = json.dumps(intent, sort_keys=True, separators=(",", ":"))
            token_ids = list(range(1, 1 + max(1, len(raw_text.encode()) // 4)))
            results.append({
                "case_id": row["case_id"], "class": row["class"], "raw_text": raw_text,
                "parsed": intent, "parse_error": None, "truth_intent": intent,
                "bound": bound, "effect": effect, "latency_ns": 1000,
                "input_tokens": 20, "output_token_ids": token_ids, "output_tokens": len(token_ids),
            })
        documents[arm] = {
            "schema": "qwen05b-abstention-balance-raw-arm-v1",
            "arm": arm, "adapter": arm != "base", "seed": FORMAL_SEED,
            "dataset_sha256": digest, "results": results,
        }
    return raw_bytes, documents


class IndependentRawAuditTests(unittest.TestCase):
    def test_reconstructs_complete_synthetic_raw_row_set(self):
        raw_bytes, documents = fixture()
        result = audit(raw_bytes, documents)
        self.assertTrue(result["integrity_pass"], result["errors"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["metrics"]["balanced"], {"exact": 64, "n": 64})

    def test_rejects_missing_row_and_reordered_rows(self):
        raw_bytes, documents = fixture()
        documents["balanced"]["results"].pop()
        self.assertIn("balanced:row_count", audit(raw_bytes, documents)["errors"])
        raw_bytes, documents = fixture()
        documents["balanced"]["results"].reverse()
        self.assertIn("balanced:row_identity_or_order", audit(raw_bytes, documents)["errors"])

    def test_rejects_raw_text_parse_mismatch(self):
        raw_bytes, documents = fixture()
        documents["base"]["results"][0]["raw_text"] = "{}"
        self.assertIn("base:row0:parse_binding", audit(raw_bytes, documents)["errors"])

    def test_rejects_forged_binding_and_effect(self):
        raw_bytes, documents = fixture()
        documents["imbalanced"]["results"][0]["bound"] = {"status": "BOUND", "name": "CLICK", "arguments": {}}
        errors = audit(raw_bytes, documents)["errors"]
        self.assertIn("imbalanced:row0:bound_reconstruction", errors)
        raw_bytes, documents = fixture()
        documents["balanced"]["results"][0]["effect"] = {"changed": True}
        self.assertIn("balanced:row0:effect_reconstruction", audit(raw_bytes, documents)["errors"])

    def test_rejects_dataset_seed_and_token_receipt_mutations(self):
        raw_bytes, documents = fixture()
        documents["balanced"]["seed"] += 1
        self.assertIn("balanced:formal_seed", audit(raw_bytes, documents)["errors"])
        raw_bytes, documents = fixture()
        documents["base"]["results"][0]["output_tokens"] += 1
        self.assertIn("base:row0:token_count", audit(raw_bytes, documents)["errors"])

    def test_reports_valid_but_inexact_intent_without_integrity_error(self):
        raw_bytes, documents = fixture()
        row = documents["balanced"]["results"][0]
        row["parsed"] = {"op": "yield", "reason": "unsupported"}
        row["raw_text"] = json.dumps(row["parsed"])
        first = build(FORMAL_SEED, SUPPORT_SEED, ALLOCATION)["heldout"][0]
        row["bound"] = reference_bind(row["parsed"], first["state"], first["requested_generation"])
        row["effect"] = reference_effect(row["bound"], first["state"])
        result = audit(raw_bytes, documents)
        self.assertTrue(result["integrity_pass"], result["errors"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["metrics"]["balanced"], {"exact": 63, "n": 64})

    def test_rejects_consistent_class_relabeling_in_pools_and_selected_rows(self):
        data = build(FORMAL_SEED, SUPPORT_SEED, ALLOCATION)
        swap = {"yield:forbidden": "yield:ambiguous", "yield:ambiguous": "yield:forbidden"}
        for pool_name in ("support_pool", "heldout_pool"):
            for row in data[pool_name]:
                row["class"] = swap.get(row["class"], row["class"])

        imbalanced_by_class, balanced_by_class = select_support(data["support_pool"], SUPPORT_SEED)
        data["supports"] = {
            "imbalanced": [row for name in CLASSES for row in imbalanced_by_class[name]],
            "balanced": [row for name in CLASSES for row in balanced_by_class[name]],
        }
        grouped = defaultdict(list)
        for row in data["heldout_pool"]:
            grouped[row["class"]].append(row)
        data["heldout"] = [row for name in CLASSES for row in grouped[name][:8]]
        raw_bytes = (json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n").encode()
        digest = hashlib.sha256(raw_bytes).hexdigest()
        documents = {}
        for arm in ("base", "imbalanced", "balanced"):
            results = []
            for row in data["heldout"]:
                intent = row["intent"]
                bound = reference_bind(intent, row["state"], row["requested_generation"])
                effect = reference_effect(bound, row["state"])
                raw_text = json.dumps(intent, sort_keys=True, separators=(",", ":"))
                token_ids = list(range(1, 1 + max(1, len(raw_text.encode()) // 4)))
                results.append({
                    "case_id": row["case_id"], "class": row["class"], "raw_text": raw_text,
                    "parsed": intent, "parse_error": None, "truth_intent": intent,
                    "bound": bound, "effect": effect, "latency_ns": 1000,
                    "input_tokens": 20, "output_token_ids": token_ids, "output_tokens": len(token_ids),
                })
            documents[arm] = {
                "schema": "qwen05b-abstention-balance-raw-arm-v1", "arm": arm,
                "adapter": arm != "base", "seed": FORMAL_SEED,
                "dataset_sha256": digest, "results": results,
            }
        result = audit(raw_bytes, documents)
        self.assertFalse(result["integrity_pass"])
        self.assertTrue(any(error.startswith("support_class_mismatch:") for error in result["errors"]))
        self.assertTrue(any(error.startswith("heldout_class_mismatch:") for error in result["errors"]))

    def test_rejects_unhashable_operation_values_without_crashing(self):
        data = build(FORMAL_SEED, SUPPORT_SEED, ALLOCATION)
        data["support_pool"][0]["intent"]["op"] = []
        data["heldout_pool"][0]["intent"]["op"] = {"malformed": True}
        raw_bytes = (json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n").encode()
        result = audit(raw_bytes, {})
        self.assertFalse(result["integrity_pass"])
        self.assertTrue(any(error.startswith("support_class_mismatch:") for error in result["errors"]))
        self.assertTrue(any(error.startswith("heldout_class_mismatch:") for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
