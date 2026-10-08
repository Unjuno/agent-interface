"""CPU controls for the independent data auditor; no formal output is generated."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
SOURCE = PACKAGE.parent / "qwen05b_abstention_balance_5139_v1"
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(PACKAGE))

from audit import ALLOCATION, audit  # noqa: E402
from make_dataset import build  # noqa: E402

TEST_SEEDS = (912001, 912007, 912011)


class IndependentAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = build(*TEST_SEEDS)
        cls.document["allocation"] = ALLOCATION

    def test_independent_reconstruction_passes_test_fixture(self) -> None:
        self.assertEqual(audit(copy.deepcopy(self.document), expected_seeds=TEST_SEEDS), [])

    def test_five_frozen_corruptions_are_rejected(self) -> None:
        corruptions = []

        item = copy.deepcopy(self.document)
        item["support_pool"].pop()
        corruptions.append(item)

        item = copy.deepcopy(self.document)
        item["supports"]["balanced"][0]["case_id"] = "forged-case"
        corruptions.append(item)

        item = copy.deepcopy(self.document)
        item["heldout"][0]["task"] += " forged"
        corruptions.append(item)

        item = copy.deepcopy(self.document)
        item["support_seed"] += 1
        corruptions.append(item)

        item = copy.deepcopy(self.document)
        item["allocation"] = "other-allocation"
        corruptions.append(item)

        self.assertEqual(len(corruptions), 5)
        self.assertTrue(all(audit(item, expected_seeds=TEST_SEEDS) for item in corruptions))


if __name__ == "__main__":
    unittest.main(verbosity=2)
