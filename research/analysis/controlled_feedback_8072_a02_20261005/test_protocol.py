import copy, unittest
import candidate, auditor


def raw_fixture():
    return {"schema":"issue8072-finite-a02-v1", "seeds":100,
            "arms":[candidate.run_arm(s,a) for s in range(100) for a in ("FULL","CONTROLLED")]}


class A02Tests(unittest.TestCase):
    def test_expected_finite_result(self):
        result = auditor.audit(raw_fixture())
        self.assertEqual(result["decision"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["errors"], [])

    def test_mutation_controls_reject_forged_feedback_identity_safety_and_order(self):
        for arm_index, query_index, field, value in (
            (0, 0, "feedback", {"utility_rows":999}),
            (1, 0, "proposal", {"kind":"TRANSFER_STRATUM","target":3}),
            (0, 6, "exact_safety_disclosed", False),
            (1, 1, "fresh_read", True)):
            altered = copy.deepcopy(raw_fixture())
            altered["arms"][arm_index]["queries"][query_index][field] = value
            self.assertTrue(auditor.audit(altered)["errors"], (arm_index, field))


if __name__ == "__main__": unittest.main()
