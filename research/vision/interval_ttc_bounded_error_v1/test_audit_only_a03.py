"""Construction mutation checks for the A03 audit-only reader."""

import copy
import pathlib
import unittest

from audit_only_a03 import audit_rows, estimate_prefix, read_jsonl, verify_manifest


ROOT = pathlib.Path(__file__).resolve().parent
A02 = ROOT / "results" / "FORMAL_A02"


class PrefixAuditMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public = read_jsonl(A02 / "public" / "public.jsonl")
        cls.oracle = read_jsonl(A02 / "oracle" / "oracle.jsonl")
        cls.candidate = read_jsonl(A02 / "candidate" / "candidate.jsonl")

    def assert_rejected(self, public=None, oracle=None, candidate=None):
        errors = audit_rows(public or self.public, oracle or self.oracle,
                            candidate or self.candidate)
        self.assertTrue(errors, "corrupted raw rows were accepted")
        return errors

    def test_unmodified_raw_reconciles_all_prefixes(self):
        self.assertEqual([], audit_rows(self.public, self.oracle, self.candidate))

    def test_future_missing_samples_do_not_invalidate_prior_prefix(self):
        truth = next(row for row in self.oracle if row["profile"] == "occlusion")
        public = next(row for row in self.public if row["id"] == truth["id"])
        history = copy.deepcopy(public["history"])
        prefix_result = estimate_prefix(history[:2])
        history[-2]["radius_px"] = None
        history[-1]["radius_px"] = None
        self.assertEqual(prefix_result, estimate_prefix(history[:2]))

    def test_bound_mutation_rejected(self):
        public = copy.deepcopy(self.public)
        target = next(row for row in public if row["history"][1]["radius_px"] is not None)
        target["history"][1]["bound_px"] += 0.25
        self.assertTrue(any("interval_mismatch" in error for error in
                            self.assert_rejected(public=public)))

    def test_timestamp_mutation_rejected(self):
        public = copy.deepcopy(self.public)
        public[0]["history"][1]["t_s"] += 0.005
        self.assert_rejected(public=public)

    def test_removed_sample_rejected(self):
        public = copy.deepcopy(self.public)
        public[0]["history"].pop(3)
        self.assertTrue(any(error.startswith("prefix_count:") for error in
                            self.assert_rejected(public=public)))

    def test_oracle_hazard_label_rejected(self):
        oracle = copy.deepcopy(self.oracle)
        oracle[0]["hazard"] = not oracle[0]["hazard"]
        self.assertTrue(any("profile_hazard_balance" in error for error in
                            self.assert_rejected(oracle=oracle)))

    def test_interval_endpoint_mutation_rejected(self):
        candidate = copy.deepcopy(self.candidate)
        estimate = next(e for row in candidate for e in row["estimates"]
                        if e["interval_s"] is not None)
        estimate["interval_s"][1] += 0.1
        self.assertTrue(any("interval_mismatch" in error for error in
                            self.assert_rejected(candidate=candidate)))

    def test_original_source_and_artifact_manifests_match(self):
        repo = ROOT.parents[2]
        source_ok, source_errors = verify_manifest(repo, A02 / "SOURCE_SHA256.txt")
        artifact_ok, artifact_errors = verify_manifest(repo, A02 / "ARTIFACT_SHA256.txt")
        self.assertTrue(source_ok, source_errors)
        self.assertTrue(artifact_ok, artifact_errors)


if __name__ == "__main__":
    unittest.main()
