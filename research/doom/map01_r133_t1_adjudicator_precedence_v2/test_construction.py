import itertools
import unittest

import audit
import decision
from formal_candidate import identity_cases


class ConstructionTests(unittest.TestCase):
    def test_all_729_sign_patterns_agree(self):
        for vector in itertools.product((-1, 0, 1), repeat=6):
            progress, exposure = tuple(vector[:3]), tuple(vector[3:])
            self.assertEqual(decision.classify(progress, exposure), audit.oracle(progress, exposure))

    def test_identity_precedence_controls(self):
        cases = identity_cases()
        expected = [
            "IDENTITY_OK",
            "identity_mismatch:model_contract_sha256",
            "identity_missing:model_contract_sha256",
            "identity_format:model_contract_sha256",
        ]
        self.assertEqual([decision.validate_identities(x["rows"]) for x in cases], expected)
        self.assertEqual([audit.identity_oracle(x["rows"]) for x in cases], expected)

    def test_malformed_value_precedes_unequal_valid_peers(self):
        rows = identity_cases()[-1]["rows"]
        self.assertEqual(decision.validate_identities(rows), "identity_format:model_contract_sha256")
        self.assertEqual(audit.identity_oracle(rows), "identity_format:model_contract_sha256")

    def test_out_of_domain_rejected(self):
        with self.assertRaisesRegex(ValueError, "sign_out_of_domain"):
            decision.classify((2, 0, 0), (0, 0, 0))


if __name__ == "__main__":
    unittest.main(verbosity=2)
