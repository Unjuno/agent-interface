from __future__ import annotations

import multiprocessing as mp
import os
import tempfile
import unittest
from pathlib import Path

from run_mp_experiment import _run_trial


class MultiProcessClaimTests(unittest.TestCase):
    def test_two_independent_spawn_workers_reproduce_baseline_race(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = _run_trial(Path(tmp), "baseline", 0)
        self.assertEqual(result["candidate_count"], 2)
        self.assertEqual(result["statuses"], [0, 0])

    def test_exclusive_create_admits_one_independent_spawn_worker(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = _run_trial(Path(tmp), "exclusive", 0)
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["statuses"], [0, 2])
        self.assertTrue(result["claim_exists"])


if __name__ == "__main__":
    unittest.main()
