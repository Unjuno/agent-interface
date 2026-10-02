#!/usr/bin/env python3
"""Construction-only controls for synthetic Issue #6483 traces."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import auditor
import candidate


ROOT = Path(__file__).resolve().parent


class PrincipalBindingConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenarios = json.loads((ROOT / "scenarios.json").read_text(encoding="utf-8"))
        cls.oracle = json.loads((ROOT / "oracle.json").read_text(encoding="utf-8"))
        cls.rows = [candidate.evaluate(policy, scenario) for scenario in cls.scenarios["scenarios"] for policy in cls.scenarios["policies"]]
        cls.raw = {
            "assigned_count": len(cls.rows),
            "input_sha256": {"scenarios.json": hashlib.sha256((ROOT / "scenarios.json").read_bytes()).hexdigest()},
            "rows": cls.rows,
        }
        cls.audit = auditor.audit_bundle(cls.scenarios, cls.oracle, cls.raw)

    def test_all_scenario_policy_assignments_retained(self):
        self.assertEqual(len(self.rows), 36)
        self.assertEqual(len({row["row_id"] for row in self.rows}), 36)

    def test_gate_preserves_clean_and_explicit_joint_requests(self):
        gate = {row["scenario_id"]: row for row in self.rows if row["policy"] == "segment_principal_gate"}
        self.assertEqual(gate["clean-single"]["disposition"], "ACTIONABLE")
        self.assertEqual(gate["cluster-switch"]["disposition"], "ACTIONABLE")
        self.assertEqual(gate["joint-authorized"]["disposition"], "ACTIONABLE_JOINT")

    def test_gate_holds_mixed_stale_unknown_and_ungranted_sources(self):
        gate = {row["scenario_id"]: row for row in self.rows if row["policy"] == "segment_principal_gate"}
        self.assertEqual(gate["overlap-negation"]["disposition"], "YIELD_MIXED_PRINCIPAL_CONTEXT")
        self.assertEqual(gate["stale-replay"]["disposition"], "SOURCE_UNKNOWN")
        self.assertEqual(gate["cluster-without-auth"]["disposition"], "SOURCE_UNKNOWN")
        self.assertEqual(gate["joint-without-grant"]["disposition"], "YIELD_JOINT_AUTHORITY")

    def test_quote_is_not_actionable(self):
        rows = [row for row in self.rows if row["scenario_id"] == "quoted-command"]
        self.assertTrue(all(row["disposition"] == "NON_ACTIONABLE_QUOTED" for row in rows))

    def test_naive_baselines_expose_wrong_or_unauthenticated_proposals(self):
        result = self.audit["baseline"]["summary"]
        self.assertGreater(result["wrong_principal_actionable_by_policy"]["transcript_order"], 0)
        self.assertGreater(result["wrong_principal_actionable_by_policy"]["cluster_only"], 0)
        self.assertGreater(result["cluster_only_unauthenticated_actionable"], 0)
        self.assertEqual(result["segment_gate_wrong_principal_actionable"], 0)

    def test_independent_oracle_and_all_four_mutations(self):
        self.assertEqual(self.audit["decision"], "METHOD_PASS_SCOPED")
        self.assertTrue(all(self.audit["corruption_controls"].values()))
        self.assertTrue(self.audit["corruption_controls"]["assigned_denominator_mutation_rejected"])

    def test_cli_roundtrip_is_construction_only(self):
        with tempfile.TemporaryDirectory() as temp:
            candidate_path, audit_path = Path(temp) / "candidate.json", Path(temp) / "audit.json"
            cand = subprocess.run([sys.executable, str(ROOT / "candidate.py"), "--scenarios", str(ROOT / "scenarios.json"), "--output", str(candidate_path)], cwd=ROOT, capture_output=True, check=False)
            self.assertEqual(cand.returncode, 0, cand.stderr.decode(errors="replace"))
            aud = subprocess.run([sys.executable, str(ROOT / "auditor.py"), "--scenarios", str(ROOT / "scenarios.json"), "--oracle", str(ROOT / "oracle.json"), "--candidate", str(candidate_path), "--output", str(audit_path)], cwd=ROOT, capture_output=True, check=False)
            self.assertEqual(aud.returncode, 0, aud.stderr.decode(errors="replace"))
            self.assertEqual(json.loads(audit_path.read_text(encoding="utf-8"))["decision"], "METHOD_PASS_SCOPED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
