import copy
import itertools
import json
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "results/review-correction-04"))
from audit import order_preference, rank_vector_orders, report_domain
from recheck_sincere_reports import (frozen_blobs_match, manifest_bytes_match,
                                     sincere_metadata_mismatches)
import recheck_sincere_reports as recheck_module


class SincereReportRecheckTests(unittest.TestCase):
    def setUp(self):
        self.orders = rank_vector_orders(["a", "b"])
        self.reports = report_domain(self.orders, [["a", "b"], []])
        self.document = {"deviations": []}
        for indices in itertools.product(range(len(self.orders)), repeat=2):
            for reporter in range(2):
                expected = next(row["report_id"] for row in self.reports
                                if row["label"] == "full"
                                and row["preference"] == order_preference(self.orders[indices[reporter]][0]))
                for report in self.reports:
                    self.document["deviations"].append({
                        "order_indices": list(indices), "reporter": reporter,
                        "report_id": report["report_id"], "sincere_report_id": expected,
                        "is_sincere": report["report_id"] == expected,
                    })

    def test_reconstructed_sincere_ids_accept_valid_document(self):
        self.assertEqual(sincere_metadata_mismatches(self.document, self.orders, self.reports), [])

    def test_candidate_chosen_sincere_ids_are_rejected(self):
        damaged = copy.deepcopy(self.document)
        first = damaged["deviations"][0]
        first["sincere_report_id"] = next(
            row["report_id"] for row in self.reports
            if row["report_id"] != first["sincere_report_id"]
        )
        self.assertTrue(sincere_metadata_mismatches(damaged, self.orders, self.reports))

    def test_sincerity_flag_is_reconstructed_too(self):
        damaged = copy.deepcopy(self.document)
        damaged["deviations"][0]["is_sincere"] = not damaged["deviations"][0]["is_sincere"]
        self.assertTrue(sincere_metadata_mismatches(damaged, self.orders, self.reports))

    def test_imported_semantic_sources_must_match_frozen_worktree_index_and_head(self):
        frozen = b"frozen audit implementation"
        digest = __import__("hashlib").sha256(frozen).hexdigest()
        self.assertTrue(frozen_blobs_match(digest, (frozen, frozen, frozen)))
        self.assertFalse(frozen_blobs_match(digest, (frozen, b"staged replacement", frozen)))

    def test_summary_manifest_must_match_worktree_index_head_and_sidecar(self):
        manifest = b"sealed evidence manifest\n"
        digest = __import__("hashlib").sha256(manifest).hexdigest()
        self.assertTrue(manifest_bytes_match(digest, (manifest, manifest, manifest), digest))
        self.assertFalse(manifest_bytes_match(digest, (b"edited manifest\n", manifest, manifest), digest))
        self.assertFalse(manifest_bytes_match(digest, (manifest, manifest, manifest), "0" * 64))

    def test_unsealed_evidence_prevents_summary_recomputation(self):
        output = Path(recheck_module.ROOT) / "results/review-correction-04/RECHECK.json"
        original = output.read_bytes()
        try:
            with patch.object(recheck_module, "verify_review03_manifest",
                              return_value=([], ["candidate evidence seal mismatch"])), \
                 patch.object(recheck_module, "summarize_manipulation") as summarize:
                self.assertEqual(recheck_module.main(), 1)
                summarize.assert_not_called()
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result["disposition"], "HOLD_RECHECK_ERRORS")
            self.assertIsNone(result["independently_recomputed_manipulation_summary_after_metadata_validation"])
        finally:
            output.write_bytes(original)

if __name__ == "__main__":
    unittest.main()
