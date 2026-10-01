"""CPU-only construction checks for this allocation's fresh dataset."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMAL_DIR = ROOT / "qwen05b_abstention_balance_5139_v1"
sys.path.insert(0, str(FORMAL_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_reference import reconstruct_dataset  # noqa: E402
from allocation_runner import (DISK_RESERVE_BYTES, claim_formal_attempt,
                               has_disk_reserve)  # noqa: E402
from dataset_builder import ALLOCATION, SEEDS, build  # noqa: E402
from coverage_summary import summarize  # noqa: E402


class AllocationConstructionTests(unittest.TestCase):
    def test_fresh_allocation_identity_and_seed_contract(self):
        doc = build()
        self.assertEqual(doc["allocation"], ALLOCATION)
        self.assertEqual(doc["formal_seed"], SEEDS["formal_seed"])
        self.assertEqual(doc["support_seed"], SEEDS["support_seed"])
        self.assertEqual(doc["heldout_seed"], SEEDS["heldout_seed"])
        self.assertEqual(len(set(SEEDS.values())), 3)

    def test_pool_sizes_counts_nesting_and_disjoint_holdout(self):
        doc = build()
        self.assertEqual(len(doc["support_pool"]), 128)
        self.assertEqual(len(doc["heldout_pool"]), 256)
        self.assertEqual(len(doc["heldout"]), 64)
        self.assertEqual(len(doc["supports"]["balanced"]), 32)
        self.assertEqual(len(doc["supports"]["imbalanced"]), 32)
        self.assertFalse({r["case_id"] for r in doc["heldout"]} &
                         {r["case_id"] for arm in doc["supports"].values() for r in arm})

    def test_independent_current_main_reconstruction(self):
        self.assertEqual(reconstruct_dataset(build()), [])

    def test_changed_seed_fails_independent_reconstruction(self):
        doc = build()
        doc["support_seed"] += 1
        self.assertTrue(reconstruct_dataset(doc))

    def test_realized_coverage_is_reported_without_seed_selection(self):
        doc = build()
        report = summarize(doc, "0" * 64)
        self.assertEqual(report["support_balanced"]["template"]["set_template_1"], 2)
        self.assertEqual(report["support_imbalanced"]["template"]["set_template_3"], 2)
        self.assertEqual(report["selection_policy"],
                         "fixed preregistered seeds; realized counts reported, never used to replace seeds")

    def test_formal_attempt_is_exclusive_and_cannot_be_reclaimed(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            claim_formal_attempt(out, ALLOCATION, "a" * 64, DISK_RESERVE_BYTES)
            marker = out / "FORMAL_ATTEMPT.json"
            original = marker.read_bytes()
            with self.assertRaisesRegex(SystemExit, "STOP_FORMAL_ATTEMPT_ALREADY_CLAIMED"):
                claim_formal_attempt(out, ALLOCATION, "b" * 64, DISK_RESERVE_BYTES)
            self.assertEqual(marker.read_bytes(), original)

    def test_host_disk_reserve_fails_closed_at_exact_boundary(self):
        self.assertTrue(has_disk_reserve(DISK_RESERVE_BYTES))
        self.assertFalse(has_disk_reserve(DISK_RESERVE_BYTES - 1))
