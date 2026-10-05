#!/usr/bin/env python3
"""Pre-freeze construction checks; not a formal candidate allocation."""
import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("mrt_candidate", HERE / "candidate.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)
audit_spec = importlib.util.spec_from_file_location("mrt_audit", HERE / "audit.py")
audit = importlib.util.module_from_spec(audit_spec)
audit_spec.loader.exec_module(audit)


class ConstructionTests(unittest.TestCase):
    def test_exact_supported_paths_and_probability_mass(self):
        paths = candidate.enumerate_session("s", 1)
        self.assertEqual(sum(p["path_probability"] for p in paths), 1.0)
        self.assertGreater(len(paths), 1)
        self.assertTrue(all(ev["eligibility_basis"] == "prior_history_only"
                            for p in paths for ev in p["events"]))

    def test_assignment_can_change_later_availability(self):
        paths = candidate.enumerate_session("s", 1)
        t1_counts = {p["assignments"][0]: sum(e["time"] == 1 for e in p["events"])
                     for p in paths if len(p["assignments"]) > 0}
        self.assertIn(0, t1_counts.values())
        self.assertIn(1, t1_counts.values())

    def test_mandatory_controls_never_change(self):
        paths = candidate.enumerate_session("s", 0) + candidate.enumerate_session("s", 1)
        self.assertTrue(all(e["mandatory_controls_intact"]
                            for p in paths for e in p["events"]))

    def test_nonexecution_is_preserved_not_conditioned_away(self):
        paths = candidate.enumerate_session("low", 0)
        rows = [e for p in paths for e in p["events"]]
        self.assertTrue(any(e["assignment"] == 1 and e["execution"] == 0 for e in rows))

    def test_protocol_estimator_and_two_baselines_are_discriminating(self):
        paths = []
        candidate_paths = []
        for case in ({"session_id": "cluster-0", "latent_stratum": 0},
                     {"session_id": "cluster-1", "latent_stratum": 1}):
            paths.extend(audit.reference_paths(case))
            candidate_paths.extend(candidate.enumerate_session(
                case["session_id"], case["latent_stratum"]))
        metrics = audit.reconstruct(paths)
        independent_candidate_stats = candidate.summaries(candidate_paths)
        self.assertEqual(independent_candidate_stats,
                         {k: v for k, v in metrics.items() if not k.startswith("oracle_")})
        self.assertAlmostEqual(metrics["ipw_excursion_estimate"],
                               metrics["oracle_excursion_effect"], places=12)
        self.assertGreater(abs(metrics["unweighted_assignment_contrast"] -
                                metrics["oracle_excursion_effect"]), 1e-12)
        self.assertGreater(abs(metrics["executed_only_contrast"] -
                                metrics["oracle_excursion_effect"]), 1e-12)
        self.assertGreater(metrics["ipw_excursion_estimate"], 0)
        self.assertGreater(metrics["distal_episode_success_by_execution_policy"]["none"],
                           metrics["distal_episode_success_by_execution_policy"]["some"])
        for history in ("none", "some"):
            self.assertAlmostEqual(
                metrics["ipw_excursion_estimate_by_carryover_history"][history],
                metrics["oracle_excursion_effect_by_carryover_history"][history], places=12)

    def test_raw_auditor_rejects_support_timing_missingness_and_interference(self):
        fixture = json.loads((HERE / "fixture.json").read_text())
        paths = []
        candidate_paths = []
        for case in fixture["sessions"]:
            paths.extend(audit.reference_paths(case))
            candidate_paths.extend(candidate.enumerate_session(
                case["session_id"], case["latent_stratum"]))
        frozen_hashes = {"construction": "pre-freeze-test"}
        base = {
            "schema": "issue7834-mrt-t0-a01-raw-v1",
            "frozen_source_sha256": frozen_hashes,
            "cross_session_interference": False,
            "formal_candidate_invocations": 1,
            "formal_auditor_invocations": 0,
            "base_main": "018934cdf45fcabffcc4efe25b5c7b3d59bd459f",
            "paths": paths,
            "candidate_summary": candidate.summaries(candidate_paths),
        }
        valid, errors, _ = audit.validate(
            base, fixture, frozen_hashes, base["base_main"])
        self.assertTrue(valid, errors)
        cases = [
            ("zero_support", lambda p: p["paths"][0]["events"][0].update(propensity=0.0),
             "NONIDENTIFIABLE_ZERO_SUPPORT"),
            ("post_treatment", lambda p: p["paths"][0]["events"][0].update(
                eligibility_basis="post_assignment"), "REJECTED_POST_TREATMENT_ELIGIBILITY"),
            ("missing_window", lambda p: p["paths"][0]["events"][0].update(proximal=None),
             "MISSING_PROXIMAL_WINDOW"),
            ("interference", lambda p: p.update(cross_session_interference=True),
             "REJECTED_INTERFERENCE_VIOLATION"),
        ]
        for _, mutate, expected_error in cases:
            damaged = json.loads(json.dumps(base))
            mutate(damaged)
            accepted, mutation_errors, _ = audit.validate(
                damaged, fixture, frozen_hashes, base["base_main"])
            self.assertFalse(accepted)
            self.assertIn(expected_error, mutation_errors)


if __name__ == "__main__":
    unittest.main(verbosity=2)
