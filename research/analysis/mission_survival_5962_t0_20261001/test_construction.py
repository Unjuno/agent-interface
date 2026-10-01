import unittest
import candidate
import auditor


class ConstructionTests(unittest.TestCase):
    def test_complete_finite_population_and_exact_marginals(self):
        data = candidate.generate()
        self.assertEqual(len(data["rows"]), 3 * sum(2 ** n for n in range(1, 9)))
        self.assertEqual(auditor.audit(data), [])

    def test_equal_marginals_but_endpoint_rankings_diverge(self):
        data = candidate.generate()
        survival = auditor.summarize(data)
        n = "8"
        any_f = {k: survival[k][n]["any_failure"] for k in survival}
        burst = {k: survival[k][n]["failure_burst_2"] for k in survival}
        self.assertNotEqual(any_f["clustered"], any_f["iid"])
        self.assertNotEqual(burst["clustered"], burst["iid"])
        self.assertNotEqual(any_f["alternating"], any_f["iid"])
        self.assertNotEqual(burst["alternating"], burst["iid"])

    def test_failures_censor_but_do_not_leave_denominator(self):
        data = candidate.generate()
        failed = [r for r in data["rows"] if "F" in r["path"]]
        self.assertTrue(failed)
        self.assertTrue(all(r["endpoints"]["any_failure"]["retained_in_denominator"] for r in failed))
        self.assertTrue(any(r["endpoints"]["any_failure"]["censored"] > 0 for r in failed))

    def test_all_corruption_controls_are_effective(self):
        self.assertEqual(set(auditor.corruption_controls(candidate.generate()).values()), {True})


if __name__ == "__main__":
    unittest.main()
