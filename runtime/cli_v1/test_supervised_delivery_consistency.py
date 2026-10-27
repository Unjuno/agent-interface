import unittest
import runtime.cli_v1.test_compiled_supervised_identity as fixtures


class SupervisedDeliveryConsistencyTests(unittest.TestCase):
    def test_conflicting_delivery_stops_without_losing_release_evidence(self):
        fixture = fixtures.SupervisedIdentityTests()
        for top, nested in ((True, False), (False, True)):
            row = fixture.row()
            row["input_dispatched"] = top
            row["supervision"]["action"]["input_dispatched"] = nested
            with self.subTest(top=top, nested=nested):
                result = fixture.terminal(row)
                self.assertEqual(result["status"], "uncertain")
                self.assertNotIn("input_dispatched", result)
                self.assertTrue(result["release"]["verified"])


    def test_inner_result_conflict_and_malformed_values_stop(self):
        fixture = fixtures.SupervisedIdentityTests()
        for value in (False, "true", 1):
            row = fixture.row()
            row["supervision"]["action"]["result"] = {"input_dispatched": value}
            with self.subTest(value=value):
                result = fixture.terminal(row)
                self.assertEqual(result["status"], "uncertain")
                self.assertNotIn("input_dispatched", result)
                self.assertTrue(result["release"]["verified"])

    def test_consistent_delivery_completes(self):
        fixture = fixtures.SupervisedIdentityTests()
        row = fixture.row()
        row["supervision"]["action"]["input_dispatched"] = True
        result = fixture.terminal(row)
        self.assertEqual(result["status"], "completed")
        self.assertIs(result["input_dispatched"], True)


if __name__ == "__main__":
    unittest.main()
