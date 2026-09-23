from __future__ import annotations

import base64
import unittest

from policy import exact_max_set, top1_hard, region_scores


def enc(score: int) -> str:
    b=bytearray(32)
    for i in range(score): b[i]=1
    return base64.b64encode(bytes(b)).decode()

ZERO=base64.b64encode(bytes(32)).decode()

class ContractTests(unittest.TestCase):
    def test_unique(self):
        before=[ZERO]*4; after=[enc(3),enc(9),enc(4),enc(2)]
        self.assertEqual(top1_hard(before,after)["selected_regions"],[1])
        self.assertEqual(exact_max_set(before,after)["selected_regions"],[1])
        self.assertTrue(exact_max_set(before,after)["exclusive"])
    def test_two_way_tie(self):
        before=[ZERO]*4; after=[enc(9),enc(2),enc(9),enc(1)]
        self.assertEqual(top1_hard(before,after)["selected_regions"],[0])
        self.assertEqual(exact_max_set(before,after)["selected_regions"],[0,2])
        self.assertFalse(exact_max_set(before,after)["exclusive"])
    def test_three_way_tie(self):
        before=[ZERO]*4; after=[enc(7),enc(7),enc(1),enc(7)]
        self.assertEqual(exact_max_set(before,after)["selected_regions"],[0,1,3])
    def test_authority_false(self):
        before=[ZERO]*4; after=[enc(7),enc(7),enc(1),enc(7)]
        self.assertFalse(top1_hard(before,after)["grants_input_authority"])
        self.assertFalse(exact_max_set(before,after)["grants_input_authority"])
    def test_shape_refusal(self):
        with self.assertRaises(ValueError):
            region_scores([ZERO]*3,[ZERO]*3)
    def test_invalid_b64(self):
        with self.assertRaises(Exception):
            region_scores(["!"]*4,[ZERO]*4)

if __name__ == "__main__":
    unittest.main()
