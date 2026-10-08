import hashlib
import json
import unittest
from pathlib import Path

import independent_audit
from candidate import run

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_BYTES = (ROOT / "fixture.json").read_bytes()
FIXTURE = json.loads(FIXTURE_BYTES)
ROWS = run(FIXTURE)
RAW = b"".join((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode() for row in ROWS)
SOURCE_HASHES = {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in ("candidate.py", "run_candidate.py", "independent_audit.py")}
MANIFEST = json.dumps({"allocation": FIXTURE["allocation"], "fixture_sha256": hashlib.sha256(FIXTURE_BYTES).hexdigest(), "ledger_sha256": hashlib.sha256(RAW).hexdigest(), "row_count": len(ROWS), "source_sha256": SOURCE_HASHES}, sort_keys=True).encode()


class OpportunityConditionedAgeTests(unittest.TestCase):
    def test_independent_oracle_reconstructs_every_frozen_case(self):
        expected = [independent_audit.expected({**r, "end_time": FIXTURE["end_time"]}, FIXTURE["end_time"]) for r in FIXTURE["rows"]]
        self.assertEqual(ROWS, expected)
        self.assertEqual(len(ROWS), 18)
        self.assertEqual(independent_audit.audit(FIXTURE_BYTES, RAW, MANIFEST), [])

    def test_delivery_age_can_favor_route_that_misses_opportunity(self):
        by_id = {r["id"]: r for r in ROWS}
        a, b = by_id["witness_aoi_route_a"], by_id["witness_aoi_route_b"]
        self.assertLess(a["delivery_ages"][0]["delivery_age"], b["delivery_ages"][0]["delivery_age"])
        self.assertEqual(a["opportunity_outcome"], "RELEVANT_EFFECT_LATE")
        self.assertEqual(b["opportunity_outcome"], "RELEVANT_EFFECT_ON_TIME")

    def test_equal_onset_latency_hides_source_age_and_validity(self):
        by_id = {r["id"]: r for r in ROWS}
        a, b = by_id["witness_age_route_a"], by_id["witness_age_route_b"]
        self.assertEqual(a["onset_to_effect"], b["onset_to_effect"])
        self.assertEqual((a["source_effect_age"], b["source_effect_age"]), (7, 2))
        self.assertEqual((a["source_validity"], b["source_validity"]), ("invalidated_at_4", "valid"))

    def test_activity_without_relevant_effect_never_resets_opportunity_age(self):
        by_id = {r["id"]: r for r in ROWS}
        for name in ("frequent_irrelevant_motor_pulses", "dispatch_without_independent_effect", "unrelated_effect_does_not_close_opportunity"):
            self.assertFalse(by_id[name]["relevant_effect_reset"], name)
        self.assertEqual(by_id["unrelated_effect_does_not_close_opportunity"]["opportunity_outcome"], "MISSED_NO_RELEVANT_EFFECT")

    def test_opportunity_denominator_keeps_expiry_but_excludes_quiet_period(self):
        by_id = {r["id"]: r for r in ROWS}
        self.assertEqual(by_id["expired_before_cycle"]["opportunity_outcome"], "MISSED_NO_RELEVANT_EFFECT")
        self.assertEqual(by_id["quiet_no_intervention_needed"]["opportunity_outcome"], "NOT_APPLICABLE")

    def test_multi_observation_without_usage_attribution_withholds_age(self):
        for name in ("multiple_ancestor_lineage_unknown", "shown_observation_not_proven_used"):
            row = next(r for r in ROWS if r["id"] == name)
            self.assertEqual(row["source_effect_age_status"], "HOLD_CAUSAL_ANCESTOR_UNKNOWN")
            self.assertIsNone(row["source_effect_age_interval"])

    def test_interval_order_deadline_and_offset_uncertainty_fail_closed(self):
        by_id = {r["id"]: r for r in ROWS}
        ordered = by_id["uncertain_but_ordered_age_interval"]
        self.assertEqual(ordered["delivery_ages"][0]["delivery_age_interval"], [3, 4])
        self.assertEqual(ordered["source_effect_age_interval"], [6, 9])
        self.assertEqual(ordered["onset_to_effect_interval"], [8, 10])
        for name in ("effect_before_source_time", "uncertain_clock_offset_reverses_order"):
            self.assertIsNone(by_id[name]["source_effect_age_interval"], name)
            self.assertEqual(by_id[name]["source_effect_age_status"], "HOLD_UNORDERED_LINEAGE")
        self.assertEqual(by_id["uncertain_clock_offset_reverses_order"]["opportunity_outcome"], "UNKNOWN_CLOCK_RELATION")
        self.assertEqual(by_id["effect_interval_straddles_deadline"]["opportunity_outcome"], "UNKNOWN_CLOCK_RELATION")
        self.assertIsNone(by_id["effect_interval_straddles_deadline"]["onset_to_effect"])

    def test_mutated_or_incomplete_raw_is_rejected(self):
        for mutation in ("drop", "effect", "source", "clock"):
            rows = json.loads(json.dumps(ROWS))
            if mutation == "drop":
                rows.pop()
            else:
                row = next(r for r in rows if r["id"] == "older_valid_timely_effect")
                if mutation == "effect":
                    row["events"]["effect"] = None
                elif mutation == "source":
                    row["events"]["effect"]["lineage"][0] = "other-row-source"
                else:
                    row["events"]["clock_comparable"] = False
            raw = b"".join((json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n").encode() for r in rows)
            changed_manifest = json.loads(MANIFEST)
            changed_manifest["ledger_sha256"] = hashlib.sha256(raw).hexdigest()
            changed_manifest_bytes = json.dumps(changed_manifest, sort_keys=True).encode()
            self.assertTrue(independent_audit.audit(FIXTURE_BYTES, raw, changed_manifest_bytes), mutation)


if __name__ == "__main__":
    unittest.main()
