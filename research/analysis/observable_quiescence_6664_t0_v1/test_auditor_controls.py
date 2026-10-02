"""Pre-freeze independent-auditor checks, including adversarial corruptions."""

import copy
import unittest

import auditor
import candidate


def _row(raw, case_id):
    return next(row for row in raw["rows"] if row["case_id"] == case_id)


def _decision(row, policy, snapshot):
    return next(d for d in row["decisions"]
                if d["policy"] == policy and d["snapshot"] == snapshot)


def _resequence(row):
    row["events"].sort(key=lambda e: (e["t"], e["seq"]))
    for seq, event in enumerate(row["events"], 1):
        event["seq"] = seq
    for event in row["events"]:
        if event["kind"] == "OBSERVATION" and event.get("freshness") == "FRESH":
            event["covers_through_seq"] = event["seq"] - 1


class AuditorControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = candidate.run()

    def _assert_rejected(self, mutate):
        damaged = copy.deepcopy(self.raw)
        mutate(damaged)
        self.assertEqual("FAIL_METHOD", auditor.audit(damaged)["status"])

    def test_unmodified_candidate_has_expected_discrimination(self):
        result = auditor.audit(self.raw)
        self.assertEqual("PASS_METHOD_SCOPED", result["status"], result)
        self.assertEqual(1191, result["case_count"])
        self.assertEqual(3573, result["snapshot_count"])
        self.assertEqual(0, result["false_quiescent"]["ACCOUNTED_QUIESCENCE"])
        self.assertGreater(result["false_quiescent"]["EPOCH_ONLY"], 0)
        self.assertGreater(result["false_quiescent"]["TIME_DELAY"], 0)

    def test_forced_false_accounted_certificate_is_rejected(self):
        def mutate(raw):
            _decision(raw["rows"][0], "ACCOUNTED_QUIESCENCE", "boundary")["status"] = "QUIESCENT"
        self._assert_rejected(mutate)

    def test_old_epoch_acceptance_is_rejected(self):
        def mutate(raw):
            row = next(r for r in raw["rows"] if r["case_id"].startswith("q-"))
            late = next(e for e in row["events"] if e["kind"] == "ADMISSION"
                        and e.get("decision") == "REJECTED_STALE")
            late["decision"] = "ACCEPTED"
        self._assert_rejected(mutate)

    def test_missing_held_input_release_is_rejected(self):
        def mutate(raw):
            row = next(r for r in raw["rows"]
                       if any(e["kind"] == "INPUT_RELEASE_ACK" for e in r["events"])
                       and _decision(r, "ACCOUNTED_QUIESCENCE", "horizon")["status"] == "QUIESCENT")
            row["events"].remove(next(e for e in row["events"]
                                      if e["kind"] == "INPUT_RELEASE_ACK"))
            _resequence(row)
        self._assert_rejected(mutate)

    def test_insufficient_observation_coverage_is_rejected(self):
        def mutate(raw):
            row = next(r for r in raw["rows"]
                       if _decision(r, "ACCOUNTED_QUIESCENCE", "horizon")["status"] == "QUIESCENT"
                       and any(e["kind"] == "OBSERVATION" for e in r["events"]))
            next(e for e in row["events"] if e["kind"] == "OBSERVATION")["covers_through_seq"] = 0
        self._assert_rejected(mutate)

    def test_duplicate_operation_identity_is_rejected(self):
        def mutate(raw):
            row = next(r for r in raw["rows"]
                       if _decision(r, "ACCOUNTED_QUIESCENCE", "horizon")["status"] == "QUIESCENT"
                       if any(e["kind"] == "ADMISSION"
                              and e.get("decision") == "ACCEPTED" for e in r["events"]))
            accepted = next(e for e in row["events"] if e["kind"] == "ADMISSION"
                            and e.get("decision") == "ACCEPTED")
            duplicate = dict(accepted)
            duplicate["seq"] = accepted["seq"] + 0.5
            row["events"].append(duplicate)
            _resequence(row)
        self._assert_rejected(mutate)

    def test_wrong_generation_reconciliation_is_rejected(self):
        def mutate(raw):
            row = _row(raw, "restart_reconciled_cancel")
            next(e for e in row["events"] if e["kind"] == "RECONCILIATION_ACK")["backend_gen"] = 1
        self._assert_rejected(mutate)

    def test_missing_reconciliation_is_rejected(self):
        def mutate(raw):
            row = _row(raw, "restart_reconciled_complete")
            row["events"].remove(next(e for e in row["events"]
                                      if e["kind"] == "RECONCILIATION_ACK"))
            _resequence(row)
        self._assert_rejected(mutate)


if __name__ == "__main__":
    unittest.main()
