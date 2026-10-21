"""Construction tests for the public-observation / hidden-truth fixture split."""

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).with_name("build_fixture.py")


def load_builder():
    if not MODULE_PATH.is_file():
        return None
    spec = importlib.util.spec_from_file_location("fixture_builder_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FixtureBuilderTests(unittest.TestCase):
    def test_fixed_seed_fixture_is_deterministic_and_keeps_truth_out_of_candidate_input(self):
        builder = load_builder()
        self.assertIsNotNone(builder, "frozen fixture builder is not implemented yet")
        public, truth = builder.build_fixture(repetitions=8)
        public_again, truth_again = builder.build_fixture(repetitions=8)
        self.assertEqual(public, public_again)
        self.assertEqual(truth, truth_again)
        self.assertEqual(len(public["cohorts"]), 8 * 6)
        for cohort in public["cohorts"]:
            self.assertEqual(len(cohort["opportunities"]), 32)
            for row in cohort["opportunities"]:
                self.assertNotIn("increments", row)
                self.assertNotIn("oracle_loss", row)
                self.assertEqual(row["resolved"], "terminal_loss" in row)


if __name__ == "__main__":
    unittest.main()
