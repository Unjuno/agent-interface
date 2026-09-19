import unittest

from .gate import evaluate_region


class RelevantRegionGateTests(unittest.TestCase):
    def setUp(self):
        self.base = {
            "observation_id": "obs-7",
            "intent_epoch": 3,
            "region_id": "toolbar",
            "coverage": "COMPLETE",
            "freshness": "CURRENT",
            "effect_binding": "BOUND",
            "authority_grants": 0,
            "ambiguous": False,
        }

    def test_admits_only_current_complete_bound_region(self):
        decision = evaluate_region(
            self.base, observation_id="obs-7", intent_epoch=3, region_id="toolbar"
        )
        self.assertEqual((decision.admitted, decision.reason), (True, "admitted"))

    def test_fail_open_controls(self):
        controls = (
            ("observation_id", "obs-old", "stale_observation"),
            ("intent_epoch", 2, "stale_intent"),
            ("region_id", "canvas", "region_mismatch"),
            ("coverage", "PARTIAL", "incomplete_coverage"),
            ("freshness", "STALE", "stale_freshness"),
            ("effect_binding", "UNBOUND", "unbound_effect"),
            ("authority_grants", 1, "authority_present"),
            ("ambiguous", True, "ambiguous"),
        )
        for key, value, reason in controls:
            with self.subTest(key=key):
                evidence = dict(self.base)
                evidence[key] = value
                decision = evaluate_region(
                    evidence,
                    observation_id="obs-7",
                    intent_epoch=3,
                    region_id="toolbar",
                )
                self.assertEqual((decision.admitted, decision.reason), (False, reason))

    def test_malformed_and_missing_fields_escalate(self):
        self.assertFalse(
            evaluate_region(None, observation_id="obs-7", intent_epoch=3, region_id="toolbar").admitted
        )
        evidence = dict(self.base)
        del evidence["coverage"]
        decision = evaluate_region(
            evidence, observation_id="obs-7", intent_epoch=3, region_id="toolbar"
        )
        self.assertEqual((decision.admitted, decision.reason), (False, "incomplete_coverage"))

    def test_source_window_binding_rejects_forgery(self):
        evidence = dict(self.base, source_window="window-actual")
        self.assertEqual(
            evaluate_region(
                evidence, observation_id="obs-7", intent_epoch=3,
                region_id="toolbar", trusted_source_window="window-forged"
            ),
            type(evaluate_region(
                evidence, observation_id="obs-7", intent_epoch=3,
                region_id="toolbar", trusted_source_window="window-forged"
            ))(False, "source_window_mismatch"),
        )


if __name__ == "__main__":
    unittest.main()
