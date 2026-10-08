import unittest

import runner


class ConstructionTests(unittest.TestCase):
    def test_fixed_denominator_and_strata(self):
        cases = runner.build_cases()
        self.assertEqual(len(cases), 56)
        self.assertEqual({s: sum(c["stratum"] == s for c in cases)
                          for s in {c["stratum"] for c in cases}},
                         {s: 8 for s in (
                             "overlap_browser", "overlap_file", "overlap_gui",
                             "replacement_task", "stale_task", "unavailable_task",
                             "novel_mode")})

    def test_support_episodes_do_not_overlap_heldout(self):
        for case in runner.build_cases():
            support = {x for e in case["evidence"] for x in e["support_episode_ids"]}
            self.assertNotIn(case["heldout_episode_id"], support)

    def test_replacement_and_expiry_filter_before_map_selection(self):
        cases = {c["stratum"]: c for c in runner.build_cases()}
        for stratum, expected in (("replacement_task", "file"), ("stale_task", "gui")):
            proposal, _, _ = runner._proposal("VALIDATED_COMPETENCE_MAP", cases[stratum])
            self.assertEqual(proposal["adapter"], expected)
            recent, _, _ = runner._proposal("RECENT_SUCCESS_ONLY", cases[stratum])
            admitted, reason = runner._admit(cases[stratum], recent)
            self.assertFalse(admitted)
            self.assertIn(reason, ("ADAPTER_VERSION_STALE", "EVIDENCE_VERSION_STALE",
                                   "EVIDENCE_EXPIRED"))

    def test_self_report_is_not_competence_evidence(self):
        case = next(c for c in runner.build_cases() if c["stratum"] == "overlap_file")
        recent, _, _ = runner._proposal("RECENT_SUCCESS_ONLY", case)
        self.assertEqual(recent["adapter"], "browser")
        self.assertEqual(runner._admit(case, recent), (False, "EVIDENCE_UNTRUSTED"))
        mapped, _, _ = runner._proposal("VALIDATED_COMPETENCE_MAP", case)
        self.assertEqual(mapped["adapter"], "file")

    def test_unavailable_and_novel_routes_yield_safely(self):
        cases = {c["stratum"]: c for c in runner.build_cases()}
        unavailable, _, _ = runner._proposal("VALIDATED_COMPETENCE_MAP",
                                             cases["unavailable_task"])
        self.assertEqual(unavailable["adapter"], "browser")
        novel, _, _ = runner._proposal("VALIDATED_COMPETENCE_MAP", cases["novel_mode"])
        self.assertIsNone(novel)
        self.assertEqual(runner._admit(cases["novel_mode"], novel),
                         (False, "YIELD_NO_PROPOSAL"))

    def test_no_policy_grants_authority_or_emits_input(self):
        case = next(c for c in runner.build_cases() if c["stratum"] == "overlap_browser")
        for policy in ("STATIC_SCOPE", "RECENT_SUCCESS_ONLY", "VALIDATED_COMPETENCE_MAP"):
            proposal, _, _ = runner._proposal(policy, case)
            result = runner._admit(case, proposal)
            self.assertIsInstance(result[0], bool)
            self.assertEqual(set(result[1:]), {"ADVISORY_ONLY"} if result[0] else
                             {"YIELD_NO_PROPOSAL"})


if __name__ == "__main__":
    unittest.main()
