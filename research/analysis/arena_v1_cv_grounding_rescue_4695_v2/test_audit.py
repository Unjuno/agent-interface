#!/usr/bin/env python3
"""Independent-oracle geometry and held-out construction checks."""
import sys
import unittest
from pathlib import Path
from audit import eligible_boxes, iou
DATA_ROOT=Path(sys.argv.pop(1)) if len(sys.argv)>1 else None

class AuditTests(unittest.TestCase):
    def test_iou_exact_and_disjoint(self):
        self.assertEqual(iou([0,0,10,10],[0,0,10,10]),1.0)
        self.assertEqual(iou([0,0,10,10],[20,20,30,30]),0.0)

    def test_heldout_component_counts(self):
        if DATA_ROOT is None:
            self.skipTest("dataset path not supplied during source-only checks")
        root=DATA_ROOT
        expected={"heldout-01-positive-min-area":1,"heldout-02-positive-low":1,
                  "heldout-03-positive-mid":1,"heldout-04-positive-max":1,
                  "heldout-05-absent":0,"heldout-06-circle":0,"heldout-07-diamond":0,
                  "heldout-08-thin-rectangle":0,"heldout-09-ambiguous-two":2,
                  "heldout-10-ambiguous-three":3,"heldout-11-ambiguous-four":4,
                  "heldout-12-ambiguous-edge":2}
        for name,count in expected.items():
            with self.subTest(name=name):
                self.assertEqual(len(eligible_boxes(root/f"{name}.png")),count)

if __name__=="__main__": unittest.main()
