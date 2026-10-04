from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from audit_a02 import AuditFailure, audit_raw

HERE = Path(__file__).resolve().parent


class A02AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads((HERE / "SOURCE/A01/RAW.json").read_text(encoding="utf-8"))
        cls.freeze = json.loads((HERE / "SOURCE/A01/FREEZE.json").read_text(encoding="utf-8"))

    def check_mutation_rejected(self, mutate):
        damaged = copy.deepcopy(self.raw)
        mutate(damaged)
        with self.assertRaises(AuditFailure):
            audit_raw(damaged, self.freeze)

    def test_retained_raw_passes_stronger_bracket_audit(self):
        result = audit_raw(copy.deepcopy(self.raw), self.freeze)
        self.assertEqual(result["disposition"], "PASS_AUDITED_GAP_REPRODUCED")
        self.assertTrue(result["release_timing_inside_sample_bracket"])

    def test_unavailable_or_errored_samples_rejected(self):
        self.check_mutation_rejected(lambda r: self.release(r)["pre_sample"].update(available=False))
        self.check_mutation_rejected(lambda r: self.release(r)["post_sample"].update(error="query failed"))

    def test_non_transitioning_samples_rejected(self):
        self.check_mutation_rejected(lambda r: self.release(r)["pre_sample"].update(down=False))
        self.check_mutation_rejected(lambda r: self.release(r)["post_sample"].update(down=True))

    def test_sample_and_release_timing_corruption_rejected(self):
        self.check_mutation_rejected(lambda r: self.release(r)["pre_sample"].update(
            started_ns=self.release(r)["pre_sample"]["finished_ns"] + 1))
        self.check_mutation_rejected(lambda r: self.release(r).update(
            release_request_ns=self.release(r)["pre_sample"]["finished_ns"] - 1))
        self.check_mutation_rejected(lambda r: self.release(r).update(
            sync_return_ns=self.release(r)["post_sample"]["finished_ns"] + 1))

    def test_invalid_down_edge_brackets_rejected(self):
        self.check_mutation_rejected(lambda r: r["bridge_emitted_events"][0][
            "physical_key_measurement"]["pre_sample"].update(available=False))
        self.check_mutation_rejected(lambda r: r["bridge_emitted_events"][0][
            "physical_key_measurement"]["pre_sample"].update(down=True))
        self.check_mutation_rejected(lambda r: r["bridge_emitted_events"][0][
            "physical_key_measurement"].update(sync_return_ns=
                r["bridge_emitted_events"][0]["physical_key_measurement"]["post_sample"]["finished_ns"] + 1))
        self.check_mutation_rejected(lambda r: r["bridge_emitted_events"][0][
            "physical_key_measurement"]["bracket"].update(key="other"))

    def test_identity_authority_and_effect_corruption_rejected(self):
        self.check_mutation_rejected(lambda r: self.release(r).update(actuation_id="other"))
        self.check_mutation_rejected(lambda r: self.release(r).update(grants_input_authority=True))
        self.check_mutation_rejected(lambda r: self.release(r).update(application_consumption_observed=True))

    @staticmethod
    def release(raw):
        return raw["owner_cleanup_record"]["per_key_release_measurements"][0]


if __name__ == "__main__":
    unittest.main()
