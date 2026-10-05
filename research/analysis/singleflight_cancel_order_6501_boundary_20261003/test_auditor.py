import unittest

import auditor
import run_candidate


class AuditContract(unittest.TestCase):
    def setUp(self):
        self.raw = run_candidate.run()
        self.digest = self.raw["source_sha256"]

    def test_all_assignments_reconstruct(self):
        result = auditor.audit(self.raw, self.digest)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["waiter_decisions"], 384)
        self.assertEqual(result["counts"]["retained_timestamp_lt"]["wrong_admit"], 48)
        self.assertEqual(result["counts"]["conservative_timestamp_le"]["wrong_reject"], 48)
        self.assertEqual(result["counts"]["ordered"], {"wrong_admit": 0, "wrong_reject": 0})

    def test_every_control_is_effective_and_rejected(self):
        controls = list(auditor.mutations(self.raw))
        self.assertEqual(len(controls), 8)
        for name, mutation in controls:
            with self.subTest(name=name):
                self.assertNotEqual(mutation, self.raw)
                self.assertTrue(auditor.audit(mutation, self.digest)["errors"])


if __name__ == "__main__":
    unittest.main()
