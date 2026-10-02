#!/usr/bin/env python3
"""CPU-only construction checks; no CUDA import, model, network or Docker."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("allocation_prepare", ROOT / "prepare.py")
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class DatasetContract(unittest.TestCase):
    def test_exact_strata_and_ids(self):
        rows = prepare.build_rows()
        self.assertEqual(len(rows), 1024)
        self.assertEqual(len({r["id"] for r in rows}), 1024)
        self.assertEqual({s: sum(r["stratum"] == s for r in rows) for s in prepare.STRATA},
                         {s: 256 for s in prepare.STRATA})

    def test_generation_is_deterministic_and_fresh_seed(self):
        self.assertEqual(prepare.SEED, 49720261010)
        self.assertNotEqual(prepare.SEED, 49720261008)
        self.assertEqual(prepare.build_rows(), prepare.build_rows())

    def test_stratum_typed_flags(self):
        for row in prepare.build_rows():
            self.assertIs(type(row["confidence_milli"]), int)
            self.assertTrue(0 <= row["confidence_milli"] <= 1000)
            self.assertIs(type(row["ambiguous"]), bool)
            self.assertIs(type(row["forced_yield"]), bool)
            if row["stratum"] == "stale": self.assertNotEqual(row["observed_sequence"], row["current_sequence"])
            if row["stratum"] == "ambiguous": self.assertTrue(row["ambiguous"])
            if row["stratum"] == "forced_yield": self.assertTrue(row["forced_yield"])


if __name__ == "__main__":
    unittest.main()

