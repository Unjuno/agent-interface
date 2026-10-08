import copy
import hashlib
import json
import unittest
from pathlib import Path

import audit
import candidate


HERE = Path(__file__).resolve().parent
SOURCE_BYTES = (HERE / "SOURCE.json").read_bytes()
SOURCE = json.loads(SOURCE_BYTES)
SOURCE_SHA256 = hashlib.sha256(SOURCE_BYTES).hexdigest()


def fresh_raw():
    return candidate.build_raw(SOURCE, SOURCE_SHA256)


class AccountingMethodContract(unittest.TestCase):
    def test_no_demand_change_preserves_session_total_and_recomputes_intensity(self):
        raw = fresh_raw()
        report = audit.audit_raw(SOURCE, raw, SOURCE_SHA256, SOURCE_BYTES)
        case = report["cases"]["no_demand_change"]
        reference = case["arms"]["reference"]
        alternate = case["arms"]["alternate"]

        self.assertEqual(reference["safe_verified_effects"], 2)
        self.assertEqual(alternate["safe_verified_effects"], 2)
        self.assertEqual(reference["client_joules_per_safe_effect"], "9000")
        self.assertEqual(alternate["client_joules_per_safe_effect"], "5400")
        self.assertEqual(reference["operational_co2e_g"]["central"], "6")
        self.assertEqual(alternate["operational_co2e_g"]["central"], "6")
        self.assertEqual(case["contrast"]["session_operational_co2e_g"]["delta_low"], "0")
        self.assertEqual(case["contrast"]["session_operational_co2e_g"]["delta_high"], "0")

    def test_beneficial_expansion_can_increase_safe_effects_and_lower_session_emissions(self):
        report = audit.audit_raw(SOURCE, fresh_raw(), SOURCE_SHA256, SOURCE_BYTES)
        case = report["cases"]["beneficial_expansion"]
        reference = case["arms"]["reference"]
        alternate = case["arms"]["alternate"]

        self.assertEqual(reference["safe_verified_effects"], 2)
        self.assertEqual(alternate["safe_verified_effects"], 3)
        self.assertEqual(reference["offered_opportunities"], 4)
        self.assertEqual(alternate["offered_opportunities"], 4)
        self.assertEqual(alternate["started_opportunities"], 4)
        self.assertEqual(alternate["operational_co2e_g"]["central"], "4.3")
        self.assertEqual(case["contrast"]["session_operational_co2e_g"]["delta_central"], "-1.7")

    def test_sign_reversal_keeps_client_intensity_and_session_total_distinct(self):
        report = audit.audit_raw(SOURCE, fresh_raw(), SOURCE_SHA256, SOURCE_BYTES)
        case = report["cases"]["seeded_sign_reversal"]
        reference = case["arms"]["reference"]
        alternate = case["arms"]["alternate"]

        self.assertLess(
            int(alternate["client_joules_per_safe_effect"]),
            int(reference["client_joules_per_safe_effect"]),
        )
        self.assertEqual(alternate["client_joules_per_safe_effect"], "3840")
        self.assertEqual(reference["operational_co2e_g"]["central"], "6")
        self.assertEqual(alternate["operational_co2e_g"]["central"], "9.1")
        self.assertEqual(case["contrast"]["session_operational_co2e_g"]["delta_low"], "2.79")
        self.assertEqual(case["contrast"]["session_operational_co2e_g"]["delta_high"], "3.41")

    def test_raw_only_auditor_rejects_omission_duplicate_boundary_denominator_and_factor_mutations(self):
        mutations = {
            "omitted energy row": lambda raw: raw["cases"]["seeded_sign_reversal"]["alternate"]["energy_rows"].pop(),
            "duplicate row": lambda raw: raw["cases"]["no_demand_change"]["reference"]["energy_rows"].append(
                copy.deepcopy(raw["cases"]["no_demand_change"]["reference"]["energy_rows"][0])
            ),
            "boundary relabel": lambda raw: raw["cases"]["no_demand_change"]["reference"]["energy_rows"][0].update(
                {"component": "combined_system"}
            ),
            "denominator mutation": lambda raw: raw["cases"]["no_demand_change"]["reference"]["reported"].update(
                {"safe_verified_effects": 3}
            ),
            "grid factor mutation": lambda raw: raw["carbon_intensity"].update(
                {"central_g_co2e_per_kwh": "5000"}
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(mutation=label):
                raw = fresh_raw()
                mutate(raw)
                with self.assertRaises(audit.AuditError):
                    audit.audit_raw(SOURCE, raw, SOURCE_SHA256, SOURCE_BYTES)


if __name__ == "__main__":
    unittest.main()
