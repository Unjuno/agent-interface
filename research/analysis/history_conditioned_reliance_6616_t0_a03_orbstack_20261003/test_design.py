import json
import hashlib
from pathlib import Path
import unittest

import audit
import candidate

ROOT = Path(__file__).resolve().parent
FIXTURE = json.loads((ROOT / "fixture.json").read_text())
ORACLE = json.loads((ROOT / "oracle.json").read_text())
FREEZE = json.loads((ROOT / "FREEZE.json").read_text())


def draft():
    receipt = {"OBSTAC_ALLOCATION_ID": candidate.ALLOCATION, "OBSTAC_SOURCE_COMMIT": "a" * 40,
               "OBSTAC_IMAGE_ID": candidate.IMAGE, "OBSTAC_FREEZE_SHA256": "b" * 64, "OBSTAC_CONSTRUCTION": "0",
               "candidate_sha256": "c" * 64, "fixture_sha256": "d" * 64}
    rows = candidate.build_rows(FIXTURE)
    raw = {"schema": "history-conditioned-reliance-candidate-raw-v1", "allocation_id": candidate.ALLOCATION,
           "execution_receipt": receipt, "row_count": len(rows), "rows": rows}
    return raw, candidate.make_packets(rows)


class StimulusDesignTests(unittest.TestCase):
    def test_freeze_binds_every_candidate_auditor_and_design_input(self):
        for name, expected in FREEZE["source_sha256"].items():
            actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, name)

    def test_equal_multiset_sequences_have_distinct_order_roles(self):
        candidate.validate_fixture(FIXTURE)
        counts = FIXTURE["expected_history_counts"]
        self.assertEqual(len({tuple(s["order"]) for s in FIXTURE["sequences"]}), 4)
        for seq in FIXTURE["sequences"]:
            self.assertEqual({k: seq["order"].count(k) for k in counts}, counts)

    def test_full_factorial_and_current_evidence_are_invariant_within_probe(self):
        raw, packets = draft()
        gates = audit.validate(FIXTURE, ORACLE, raw, packets)
        self.assertEqual(gates["rows_reconstructed"], 36)
        for probe_id in {r["probe_id"] for r in raw["rows"]}:
            current = {(json.dumps(r["current_receipt"], sort_keys=True),
                        json.dumps(r["raw_evidence"], sort_keys=True),
                        json.dumps(r["task_metadata"], sort_keys=True),
                        json.dumps(r["action_options"], sort_keys=True))
                       for r in raw["rows"] if r["probe_id"] == probe_id}
            self.assertEqual(len(current), 1)

    def test_hidden_oracle_never_enters_candidate_or_reviewer_packets(self):
        raw, packets = draft()
        self.assertFalse(audit.hidden_keys(raw))
        self.assertFalse(audit.hidden_keys(packets))
        self.assertEqual(audit.validate(FIXTURE, ORACLE, raw, packets)["human_responses"], 0)

    def test_all_four_preregistered_mutations_are_rejected(self):
        raw, packets = draft()
        results = audit.corruption_controls(FIXTURE, ORACLE, raw, packets)
        self.assertEqual(len(results), 4)
        self.assertTrue(all(value == "REJECTED" for value in results.values()))

    def test_unknown_is_not_relabelled_as_success_or_failure(self):
        statuses = {p["current_receipt"]["typed_status"] for p in FIXTURE["probes"]}
        self.assertIn("unknown_partial", statuses)
        self.assertNotIn("success", statuses)
        self.assertNotIn("failure", statuses)


if __name__ == "__main__":
    unittest.main()
