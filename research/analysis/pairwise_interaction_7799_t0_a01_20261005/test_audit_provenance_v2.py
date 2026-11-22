"""Mutation controls for the additive #7799 provenance audit."""

from __future__ import annotations

import copy
import unittest

from audit_provenance_v2 import (
    EXPECTED_AUDIT_RAW_SHA256,
    EXPECTED_AUDITOR_SOURCE_SHA256,
    EXPECTED_CANDIDATE_RAW_SHA256,
    EXPECTED_CANDIDATE_SOURCE_SHA256,
    EXPECTED_FREEZE_SHA256,
    EXPECTED_MANIFEST_SHA256,
    EXPECTED_SOURCE_COMMIT,
    PACKAGE_FILES,
    evaluate,
    mutation_checks,
)


class ProvenanceAuditTests(unittest.TestCase):
    def setUp(self):
        self.freeze = {
            "source_commit": EXPECTED_SOURCE_COMMIT,
            "source_paths": {"plan.md": "a" * 64, "protocol.py": "b" * 64},
        }
        self.freeze_sha256 = EXPECTED_FREEZE_SHA256
        self.source_hashes = dict(self.freeze["source_paths"])
        self.manifest_sha256 = EXPECTED_MANIFEST_SHA256
        self.manifest = dict(PACKAGE_FILES)
        self.package_hashes = {
            "candidate.py": EXPECTED_CANDIDATE_SOURCE_SHA256,
            "audit.py": EXPECTED_AUDITOR_SOURCE_SHA256,
            "results/formal-01/candidate.json": EXPECTED_CANDIDATE_RAW_SHA256,
            "results/formal-01/audit.json": EXPECTED_AUDIT_RAW_SHA256,
        }
        self.candidate = {
            "source_commit": self.freeze["source_commit"],
            "source_sha256": dict(self.freeze["source_paths"]),
            "eligibility": "HOLD_T0_NO_ELIGIBLE_INDEPENDENT_PAIR",
        }
        self.candidate_raw_sha256 = EXPECTED_CANDIDATE_RAW_SHA256
        self.audit = {
            "raw_sha256": self.candidate_raw_sha256,
            "decision": "PASS_AUDIT",
            "passed": 11,
            "total": 11,
            "rederived_design_matrix_rank": 2,
        }
        self.audit_raw_sha256 = EXPECTED_AUDIT_RAW_SHA256

    def inputs(self):
        return (
            self.freeze,
            self.freeze_sha256,
            self.source_hashes,
            self.manifest_sha256,
            self.manifest,
            self.package_hashes,
            self.candidate,
            self.candidate_raw_sha256,
            self.audit,
            self.audit_raw_sha256,
        )

    def test_exact_pins_pass_and_all_mutations_fail(self):
        result = evaluate(*self.inputs())
        self.assertEqual(result["disposition"], "PASS_SOURCE_BINDING_ONLY")
        checks = mutation_checks(self.inputs())
        self.assertEqual(len(checks), 7)
        self.assertTrue(all(checks.values()), checks)

    def test_candidate_and_auditor_code_bytes_are_required(self):
        package_hashes = dict(self.package_hashes)
        package_hashes["candidate.py"] = "0" * 64
        args = list(self.inputs())
        args[5] = package_hashes
        result = evaluate(*args)
        self.assertEqual(result["disposition"], "FAIL_SOURCE_BINDING_ONLY")
        self.assertFalse(result["checks"]["candidate_code_matches_a01_manifest"])

        package_hashes = dict(self.package_hashes)
        package_hashes["audit.py"] = "0" * 64
        args[5] = package_hashes
        result = evaluate(*args)
        self.assertEqual(result["disposition"], "FAIL_SOURCE_BINDING_ONLY")
        self.assertFalse(result["checks"]["original_auditor_code_matches_a01_manifest"])

    def test_freeze_and_manifest_mutations_fail(self):
        changed_freeze = copy.deepcopy(self.freeze)
        changed_freeze["source_paths"]["plan.md"] = "0" * 64
        args = list(self.inputs())
        args[0] = changed_freeze
        self.assertEqual(evaluate(*args)["disposition"], "FAIL_SOURCE_BINDING_ONLY")

        args = list(self.inputs())
        args[3] = "0" * 64
        self.assertEqual(evaluate(*args)["disposition"], "FAIL_SOURCE_BINDING_ONLY")


if __name__ == "__main__":
    unittest.main()
