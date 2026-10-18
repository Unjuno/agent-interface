"""Regression and mutation tests for strict measurement consumption."""
import copy
import json
import unittest
import tempfile
from pathlib import Path
from candidate import EvidenceError, reconstruct
from audit import independently_reconstruct, audit

HERE = Path(__file__).resolve().parent
EVENTS = [json.loads(x) for x in (HERE / "INPUT_EVENTS.jsonl").read_text().splitlines()]


class ConsumerTests(unittest.TestCase):
    def test_retained_pair_reconstructs_interval_without_authority_or_effect(self):
        got = reconstruct(EVENTS)
        self.assertEqual((got["hold_duration_lower_bound_ns"],
                          got["hold_duration_upper_bound_ns"]), (50417, 58458))
        self.assertFalse(got["authority_granted"])
        self.assertFalse(got["application_effect_observed"])
        self.assertEqual(independently_reconstruct(EVENTS), got)

    def test_actuation_alias_is_rejected(self):
        rows = copy.deepcopy(EVENTS)
        rows[1]["physical_key_measurement"]["actuation_id"] = "other"
        with self.assertRaises(EvidenceError): reconstruct(rows)

    def test_measurement_actuation_alias_is_rejected(self):
        rows = copy.deepcopy(EVENTS)
        rows[1]["physical_key_measurement"]["actuation_id"] = "other"
        with self.assertRaises(EvidenceError): reconstruct(rows)

    def test_edge_bracket_disagreement_is_rejected(self):
        rows = copy.deepcopy(EVENTS)
        rows[1]["physical_key_measurement"]["adapter_edge"]["interval"][0] += 1
        with self.assertRaises(EvidenceError): reconstruct(rows)

    def test_boolean_timestamp_is_not_integer_timestamp(self):
        rows = copy.deepcopy(EVENTS)
        rows[1]["physical_key_measurement"]["adapter_edge"]["interval"][0] = True
        with self.assertRaises(EvidenceError): reconstruct(rows)

    def test_false_authority_claim_is_rejected(self):
        rows = copy.deepcopy(EVENTS)
        rows[1]["physical_key_measurement"]["adapter_edge"]["grants_input_authority"] = True
        with self.assertRaises(EvidenceError): reconstruct(rows)

    def test_wrong_edge_intent_is_rejected(self):
        rows = copy.deepcopy(EVENTS)
        rows[1]["physical_key_measurement"]["adapter_edge"]["intent_token"] = "other"
        with self.assertRaises(EvidenceError): reconstruct(rows)

    def test_unconfirmed_release_is_not_zero_or_success(self):
        rows = copy.deepcopy(EVENTS)
        rows[1]["physical_key_measurement"]["classification"] = "RELEASE_UNCONFIRMED"
        with self.assertRaises(EvidenceError): reconstruct(rows)

    def test_reversed_or_overlapping_brackets_are_rejected(self):
        rows = copy.deepcopy(EVENTS)
        rows[1]["physical_key_measurement"]["adapter_edge"]["interval"] = [10, 11]
        rows[1]["physical_key_measurement"]["bracket"]["physical_up_interval"] = [10, 11]
        with self.assertRaises(EvidenceError): reconstruct(rows)

    def test_raw_audit_rejects_modified_candidate_interval(self):
        source = HERE / "results" / "a02" / "RESULT.json"
        payload = json.loads(source.read_text())
        payload["candidate"]["hold_duration_lower_bound_ns"] += 1
        with tempfile.TemporaryDirectory() as temporary:
            changed = Path(temporary) / "RESULT.json"
            changed.write_text(json.dumps(payload))
            result = audit(HERE / "INPUT_EVENTS.jsonl", changed)
        self.assertEqual(result["disposition"], "FAIL_MISMATCH")
        self.assertIn("candidate differs from raw reconstruction", result["errors"])

if __name__ == "__main__": unittest.main(verbosity=2)
