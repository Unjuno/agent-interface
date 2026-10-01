import copy
import unittest

import runner
import audit


def counterexample():
    return {
        "truth": False,
        "receipts": [
            {"id": "V1", "verdict": True, "visible_peer_ids": []},
            {"id": "V2", "verdict": True, "visible_peer_ids": ["V1"]},
            {"id": "V3", "verdict": False, "visible_peer_ids": []},
        ],
        "history_complete": True,
        "commitment_valid": True,
        "reported_edges_match_capture": True,
    }


class PeerVerdictTests(unittest.TestCase):
    def test_exposed_wrong_verdict_is_not_a_second_independent_vote(self):
        result = runner.adjudicate(counterexample())
        self.assertEqual(result["count_only"], "INCORRECT_QUORUM_PASS")
        self.assertEqual(result["exposure_aware"], "NO_QUORUM")
        self.assertEqual(result["independent_ids"], ["V1", "V3"])

    def test_unknown_or_inconsistent_exposure_history_fails_closed(self):
        base = counterexample()
        controls = (
            {**base, "history_complete": False},
            {**base, "commitment_valid": False},
            {**base, "reported_edges_match_capture": False},
        )
        for changed in controls:
            with self.subTest(changed=changed):
                self.assertEqual(runner.adjudicate(changed)["exposure_aware"],
                                 "UNKNOWN_INDEPENDENCE")

    def test_all_truth_verdict_graph_combinations_are_enumerated(self):
        cases = runner.enumerate_cases()
        self.assertEqual(len(cases), 128)
        self.assertEqual(len({row["case_id"] for row in cases}), 128)
        self.assertEqual(audit.audit(runner.run())["status"],
                         "PASS_T0_ENUMERATION")

    def test_auditor_rejects_dropped_row_result_change_and_exposure_erasure(self):
        raw = runner.run()
        dropped = {**raw, "rows": raw["rows"][1:]}
        self.assertEqual(audit.audit(dropped)["status"], "FAIL_RAW_INCOMPLETE")

        changed = copy.deepcopy(raw)
        changed["rows"][0]["result"]["exposure_aware"] = "INCORRECT_QUORUM_PASS"
        self.assertEqual(audit.audit(changed)["status"], "FAIL_RESULT_MISMATCH")

        erased = copy.deepcopy(raw)
        exposed = next(row for row in erased["rows"]
                       if row["receipts"][1]["visible_peer_ids"])
        exposed["receipts"][1]["visible_peer_ids"] = []
        self.assertEqual(audit.audit(erased)["status"], "FAIL_RESULT_MISMATCH")


if __name__ == "__main__":
    unittest.main()
