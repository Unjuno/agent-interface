import copy
import unittest
from fractions import Fraction as F

from audit import audit
from candidate import evaluate
from test_candidate_contract import base_case


class AuditorContractTests(unittest.TestCase):
    def test_independent_auditor_reconstructs_safe_row_and_mutations(self):
        case = base_case(
            actuator=[["1/10", "1/10"], ["1/10", "1/10"]],
            release=[["1/10", "0"], ["0", "1/10"]],
            release_factor=["1/2", "1/2"],
        )
        result = audit([case], [evaluate(case)])
        self.assertEqual(result["audit_contract"], "PASS_AUDIT_SCOPED")
        self.assertEqual(result["rows_reconstructed"], 1)
        self.assertEqual(result["mutations_rejected"], 3)

    def test_auditor_rejects_falsely_certified_coupled_escape(self):
        case = base_case(
            current=[["1/2", "0"], ["0", "1/2"]],
            actuator=[["0", "3/4"], ["3/4", "0"]],
            saturation=["8", "8"], initial=["1", "1"],
            feature_limit="2", horizon=8,
        )
        forged = evaluate(case)
        forged["disposition"] = "CERTIFIED"
        result = audit([case], [forged])
        self.assertEqual(result["disposition"], "FAIL_AUDIT")
        self.assertEqual(result["unsafe_certificates"], 1)

    def test_auditor_detects_omitted_coupling_in_claimed_gain_matrix(self):
        case = base_case(current=[["1/2", "0"], ["0", "1/2"]],
                         actuator=[["0", "1/5"], ["1/5", "0"]])
        forged = evaluate(case)
        forged["gain_matrix"] = [["1/2", "0"], ["1/5", "1/2"]]
        result = audit([case], [forged])
        self.assertEqual(result["disposition"], "FAIL_AUDIT")
        self.assertGreater(result["row_mismatches"], 0)

    def test_auditor_rejects_extra_or_missing_rows(self):
        case = base_case()
        one = evaluate(case)
        self.assertEqual(audit([case], [one, copy.deepcopy(one)])["disposition"], "FAIL_AUDIT")
        self.assertEqual(audit([case, copy.deepcopy(case)], [one])["disposition"], "FAIL_AUDIT")

    def test_auditor_applies_preregistered_case_gate_not_just_row_equality(self):
        case = base_case()
        expected = evaluate(case)
        # A raw row can match its reconstruction while the whole preregistered
        # suite still must fail if required case identifiers are absent.
        result = audit([case], [expected])
        self.assertEqual(result["disposition"], "FAIL_AUDIT")


if __name__ == "__main__":
    unittest.main()
