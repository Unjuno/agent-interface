import unittest
import hashlib
import json
import struct
from pathlib import Path

import corpus
from protocol import median_ns, score_rows, validate_result

HERE = Path(__file__).resolve().parent


class DecisionSchemaTests(unittest.TestCase):
    def test_accepts_each_declared_typed_decision(self):
        self.assertEqual(
            validate_result({
                "decision": "TARGET",
                "target": "Publish",
                "container": "Project Atlas",
                "state": "ENABLED",
                "reason": None,
            })["decision"],
            "TARGET",
        )
        self.assertEqual(
            validate_result({
                "decision": "STATE",
                "target": None,
                "container": None,
                "state": "STATUS_SAVED",
                "reason": None,
            })["state"],
            "STATUS_SAVED",
        )
        self.assertEqual(
            validate_result({
                "decision": "NO_ACTION",
                "target": None,
                "container": None,
                "state": None,
                "reason": "TARGET_ABSENT",
            })["reason"],
            "TARGET_ABSENT",
        )
        self.assertEqual(
            validate_result({
                "decision": "YIELD",
                "target": None,
                "container": None,
                "state": None,
                "reason": "AMBIGUOUS",
            })["reason"],
            "AMBIGUOUS",
        )

    def test_rejects_authority_fields_and_unexpected_keys(self):
        row = {
            "decision": "TARGET",
            "target": "Publish",
            "container": "Project Atlas",
            "state": "ENABLED",
            "reason": None,
            "authority": "granted",
        }
        with self.assertRaisesRegex(ValueError, "keys"):
            validate_result(row)

    def test_rejects_target_without_container_identity(self):
        with self.assertRaisesRegex(ValueError, "container"):
            validate_result({
                "decision": "TARGET",
                "target": "Publish",
                "container": None,
                "state": "ENABLED",
                "reason": None,
            })


class FrozenCorpusTests(unittest.TestCase):
    def test_covers_each_required_grounding_case_twice(self):
        counts = {}
        for case in corpus.CASES:
            counts[case["category"]] = counts.get(case["category"], 0) + 1
        self.assertEqual(
            counts,
            {
                "unambiguous": 2,
                "similar_distractor": 2,
                "missing_target": 2,
                "ambiguous_target": 2,
                "changed_layout": 2,
                "state_effect": 2,
                "unsupported_novel": 2,
            },
        )
        self.assertEqual(len({case["case_id"] for case in corpus.CASES}), 14)

    def test_model_inputs_are_separate_from_category_and_oracle(self):
        rows = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
        expected_keys = {"case_id", "intent", "image", "image_sha256", "width", "height"}
        self.assertEqual(len(rows), 14)
        self.assertEqual({row["case_id"] for row in rows}, {case["case_id"] for case in corpus.CASES})
        self.assertTrue(all(set(row) == expected_keys for row in rows))
        self.assertFalse(any("oracle" in row or "category" in row for row in rows))

    def test_frozen_png_manifest_matches_rgb_framebuffer_bytes(self):
        rows = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
        for row in rows:
            raw = (HERE / row["image"]).read_bytes()
            self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")
            width, height, bit_depth, color_type = struct.unpack(">IIBB", raw[16:26])
            self.assertEqual((width, height, bit_depth, color_type), (1280, 800, 8, 2))
            self.assertEqual((row["width"], row["height"]), (1280, 800))
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["image_sha256"])

    def test_oracle_has_exactly_the_frozen_safe_decision_mix(self):
        oracle = json.loads((HERE / "oracle.json").read_text(encoding="utf-8"))
        self.assertEqual(set(oracle), {case["case_id"] for case in corpus.CASES})
        counts = {}
        for result in oracle.values():
            validate_result(result)
            counts[result["decision"]] = counts.get(result["decision"], 0) + 1
        self.assertEqual(counts, {"TARGET": 6, "NO_ACTION": 2, "YIELD": 4, "STATE": 2})


class ScoringTests(unittest.TestCase):
    def test_scores_exact_typed_outputs_against_separate_oracle(self):
        expected = {
            "case-a": {
                "decision": "TARGET",
                "target": "Publish",
                "container": "Project Atlas",
                "state": "ENABLED",
                "reason": None,
            },
            "case-b": {
                "decision": "YIELD",
                "target": None,
                "container": None,
                "state": None,
                "reason": "AMBIGUOUS",
            },
        }
        observed = [
            {"case_id": "case-a", "result": expected["case-a"], "latency_ns": 100},
            {"case_id": "case-b", "result": expected["case-b"], "latency_ns": 200},
        ]
        self.assertEqual(score_rows(observed, expected), {"exact": 2, "total": 2, "wrong_target": 0})

    def test_flags_wrong_target_even_when_decision_type_is_valid(self):
        expected = {
            "case-a": {
                "decision": "TARGET",
                "target": "Publish",
                "container": "Project Atlas",
                "state": "ENABLED",
                "reason": None,
            }
        }
        observed = [{
            "case_id": "case-a",
            "result": {
                "decision": "TARGET",
                "target": "Publish",
                "container": "Project Borealis",
                "state": "ENABLED",
                "reason": None,
            },
            "latency_ns": 100,
        }]
        self.assertEqual(score_rows(observed, expected), {"exact": 0, "total": 1, "wrong_target": 1})

    def test_median_latency_uses_all_rows_and_rejects_missing_measurements(self):
        self.assertEqual(median_ns([10, 20, 30, 40]), 25)
        with self.assertRaisesRegex(ValueError, "empty"):
            median_ns([])
        with self.assertRaisesRegex(ValueError, "positive"):
            median_ns([0, 10])


if __name__ == "__main__":
    unittest.main()
