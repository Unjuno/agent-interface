"""Pre-freeze construction checks for the five-request A02 fixture."""
from __future__ import annotations

import copy
import json
import pathlib
import unittest

import audit
import candidate


ROOT = pathlib.Path(__file__).parent


class ServiceDebtAliasA02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "trace_fixture.json").read_text())
        cls.oracle = json.loads((ROOT / "outcome_oracle.json").read_text())

    def test_complete_bell_five_partition_set(self):
        observed = {audit._canonical_partition(item["blocks"]) for item in self.fixture["alias_partitions"]}
        expected = audit._all_partitions(5)
        self.assertEqual(len(expected), 52)
        self.assertEqual(observed, expected)
        self.assertEqual(self.fixture["alias_partitions"][0]["blocks"], [[0, 1, 2, 3, 4]])

    def test_candidate_and_independent_auditor_reconstruct_all_rows(self):
        raw = candidate.run(self.fixture)
        result = audit.audit(self.fixture, self.oracle, raw)
        self.assertEqual(len(raw["rows"]), 177)
        self.assertEqual(result["rows_checked"], 177)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["disposition"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["alias_summary"]["alias_partition_count"], 52)
        self.assertTrue(any(row["advantage_observed"] for row in result["alias_summary"]["alias_advantages"]))
        self.assertTrue(all(row["matches_one_identity_service_units"] for row in result["alias_summary"]["trusted_parent_replays"]))

    def test_hard_safety_controls_remain_unchanged(self):
        raw = candidate.run(self.fixture)
        result = audit.audit(self.fixture, self.oracle, raw)
        self.assertEqual(result["errors"], [])
        revoked = result["metrics"]["revoked_principal|trusted_parent_service_debt"]["service_units"]
        self.assertEqual(revoked.get("A", 0), 0)
        self.assertEqual(revoked["B"], 4)
        missing = next(row for row in raw["rows"] if row["case_id"] == "missing_joint_grant" and row["policy"] == "trusted_parent_service_debt")
        self.assertIn("J_A1", {row["request_id"] for row in missing["excluded"]})

    def test_independent_audit_rejects_five_corruptions(self):
        raw = candidate.run(self.fixture)
        mutations = []
        changed = copy.deepcopy(raw)
        row = next(row for row in changed["rows"] if row["case_id"] == "revoked_principal" and row["policy"] == "trusted_parent_service_debt")
        row["attempts"].append({"request_id": "R_A0", "caller_id": "RA", "start": 0, "end": 1, "service": 1})
        mutations.append(changed)
        changed = copy.deepcopy(raw)
        row = next(row for row in changed["rows"] if row["case_id"] == "mandatory_release" and row["policy"] == "trusted_parent_service_debt")
        row["release_events"] = []
        mutations.append(changed)
        changed = copy.deepcopy(raw)
        row = next(row for row in changed["rows"] if row["case_id"] == "false_parent_claim" and row["policy"] == "trusted_parent_service_debt")
        row["parent_claims"][0]["decision"] = "ACCEPTED"
        mutations.append(changed)
        changed = copy.deepcopy(raw)
        changed["rows"][0]["attempts"][0]["verified_useful"] = True
        mutations.append(changed)
        changed = copy.deepcopy(raw)
        changed["rows"][0]["attempts"][0]["end"] += 1
        mutations.append(changed)
        for mutated in mutations:
            self.assertTrue(audit.audit(self.fixture, self.oracle, mutated)["errors"])


if __name__ == "__main__":
    unittest.main()
