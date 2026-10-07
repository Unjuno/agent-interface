"""Ordinary retained-mini regression; no pipe/candidate/formal invocation."""
import copy
import json
from pathlib import Path
import unittest
import auditor

HERE=Path(__file__).resolve().parent
ROOT=HERE/'construction/run-01/result'


class Checks(unittest.TestCase):
    def setUp(self):
        self.raw=json.loads((ROOT/'RAW.json').read_text())
        self.deck=json.loads((HERE/'construction/deck-01.json').read_text())

    def test_complete_and_capped_mini_reconstruct(self):
        self.assertEqual(auditor.verify(self.raw,self.deck,ROOT),[])

    def test_missing_sample_is_named_refusal(self):
        changed=copy.deepcopy(self.raw);changed['rows'][0]['samples'].pop()
        self.assertIn('m00:SAMPLE_COUNT',auditor.verify(changed,self.deck,ROOT))

    def test_all_directed_controls_have_specific_reason(self):
        result=auditor.controls(self.raw,self.deck,ROOT)
        self.assertEqual(len(result),10)
        self.assertTrue(all(r['rejected_for_required_reason'] for r in result))


if __name__=='__main__':unittest.main()
