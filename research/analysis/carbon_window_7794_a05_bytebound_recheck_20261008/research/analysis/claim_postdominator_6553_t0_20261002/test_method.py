import copy
import json
import unittest
from pathlib import Path

import auditor
import candidate


class ClaimScopedPlacementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        here = Path(__file__).resolve().parent
        cls.fixture = json.loads((here / "fixture.json").read_text(encoding="utf-8"))
        cls.oracle = json.loads((here / "oracle.json").read_text(encoding="utf-8"))
        cls.raw = candidate.run(cls.fixture)

    def by_id(self, case_id):
        return next(row for row in self.raw["cases"] if row["case_id"] == case_id)

    def test_typed_shared_oracle_reduces_cost_only_on_positive_routes(self):
        row = self.by_id("positive_shared")
        self.assertEqual(row["typed"]["status"], "SHARED_CHECK_PLACED")
        self.assertEqual(row["typed"]["selected_checks"], ["shared_ab"])
        self.assertEqual(row["typed"]["total_cost"], 3.0)
        self.assertEqual(row["route_local"]["total_cost"], 6.0)
        self.assertEqual(row["graph_only"]["selected_checks"], ["dispatch_ack"])
        self.assertEqual(row["graph_only"]["total_cost"], 1.5)

    def test_no_gain_control_retains_route_local_checks(self):
        row = self.by_id("no_gain_loop_exit")
        self.assertEqual(row["typed"]["status"], "ROUTE_LOCAL_NO_GAIN")
        self.assertEqual(row["typed"]["selected_checks"], ["route_a0", "route_a1", "route_b"])
        self.assertEqual(row["typed"]["total_cost"], row["route_local"]["total_cost"])

    def test_semantic_mismatch_and_stale_receipt_refuse_shared_placement(self):
        wrong = self.by_id("wrong_target")
        stale = self.by_id("stale_generation")
        self.assertEqual(wrong["typed"]["status"], "NO_SOUND_SHARED_CHECK")
        self.assertEqual(stale["typed"]["status"], "NO_SOUND_SHARED_CHECK")
        self.assertEqual(wrong["graph_only"]["selected_checks"], ["dispatch_ack"])
        self.assertEqual(stale["graph_only"]["selected_checks"], ["dispatch_ack"])

    def test_hidden_effect_and_early_claim_are_not_repaired_by_graph_intersection(self):
        hidden = self.by_id("hidden_effect")
        early = self.by_id("early_claim")
        self.assertEqual(hidden["typed"]["status"], "NO_SOUND_SHARED_CHECK")
        self.assertEqual(early["typed"]["status"], "NO_SOUND_SHARED_CHECK")
        self.assertTrue(early["graph_only"]["claim_precedes_all_checks"])

    def test_independent_auditor_accepts_only_the_frozen_expected_dispositions(self):
        report = auditor.audit(self.fixture, self.oracle, self.raw)
        self.assertEqual(report["errors"], [])
        statuses = {row["case_id"]: row["status"] for row in report["cases"]}
        self.assertEqual(statuses, {
            "positive_shared": "PASS_TYPED_SHARED",
            "no_gain_loop_exit": "NO_COMPRESSION_GAIN",
            "wrong_target": "UNKNOWN_NO_SOUND_SHARED_CHECK",
            "stale_generation": "UNKNOWN_STALE_CHECK",
            "hidden_effect": "UNKNOWN_NO_SOUND_SHARED_CHECK",
            "incomplete_graph": "HOLD_GRAPH_INCOMPLETE",
            "early_claim": "HOLD_EARLY_CLAIM",
        })

    def test_auditor_rejects_missing_path_and_false_shared_claim(self):
        raw = copy.deepcopy(self.raw)
        positive = next(row for row in raw["cases"] if row["case_id"] == "positive_shared")
        positive["paths"].pop()
        report = auditor.audit(self.fixture, self.oracle, raw)
        self.assertTrue(any("paths" in error for error in report["errors"]))

        raw = copy.deepcopy(self.raw)
        positive = next(row for row in raw["cases"] if row["case_id"] == "positive_shared")
        positive["typed"]["selected_checks"] = ["dispatch_ack"]
        report = auditor.audit(self.fixture, self.oracle, raw)
        self.assertTrue(report["errors"])

    def test_auditor_detects_unmodeled_success_edge_from_independent_graph(self):
        row = self.by_id("incomplete_graph")
        self.assertEqual(row["typed"]["status"], "HOLD_GRAPH_INCOMPLETE")
        report = auditor.audit(self.fixture, self.oracle, self.raw)
        result = next(item for item in report["cases"] if item["case_id"] == "incomplete_graph")
        self.assertEqual(result["status"], "HOLD_GRAPH_INCOMPLETE")
        self.assertGreater(result["oracle_path_count"], result["reported_path_count"])

    def test_auditor_rejects_six_raw_or_oracle_corruptions(self):
        corruptions = []

        raw = copy.deepcopy(self.raw)
        raw["cases"].pop()
        corruptions.append((self.fixture, self.oracle, raw))

        raw = copy.deepcopy(self.raw)
        next(row for row in raw["cases"] if row["case_id"] == "positive_shared")["typed"]["selected_checks"] = ["dispatch_ack"]
        corruptions.append((self.fixture, self.oracle, raw))

        raw = copy.deepcopy(self.raw)
        next(row for row in raw["cases"] if row["case_id"] == "positive_shared")["typed"]["total_cost"] += 1
        corruptions.append((self.fixture, self.oracle, raw))

        raw = copy.deepcopy(self.raw)
        next(row for row in raw["cases"] if row["case_id"] == "early_claim")["graph_only"]["claim_certified"] = True
        corruptions.append((self.fixture, self.oracle, raw))

        raw = copy.deepcopy(self.raw)
        raw["fixture_sha256"] = "0" * 64
        corruptions.append((self.fixture, self.oracle, raw))

        oracle = copy.deepcopy(self.oracle)
        oracle["cases"]["positive_shared"]["checks"]["shared_ab"]["truth"] = False
        corruptions.append((self.fixture, oracle, self.raw))

        for index, (fixture, oracle, raw) in enumerate(corruptions, start=1):
            with self.subTest(corruption=index):
                self.assertTrue(auditor.audit(fixture, oracle, raw)["errors"])


if __name__ == "__main__":
    unittest.main()
