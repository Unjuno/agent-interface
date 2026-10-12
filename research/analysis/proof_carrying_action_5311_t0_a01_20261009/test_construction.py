import json, unittest
from pathlib import Path
from candidate import cert_check, full

ROOT=Path(__file__).parent
DATA=json.loads((ROOT/'cases.json').read_text())

class Construction(unittest.TestCase):
    def test_positive_and_negative_corpus(self):
        p=DATA['policy']
        cert_only={'negative-missing-predicate','negative-wrong-target','negative-unsupported-predicate'}
        for case in DATA['cases']:
            expected_full=case['id'].startswith('valid-') or case['id'] in cert_only
            expected_cert=case['id'].startswith('valid-')
            self.assertEqual(full(case['plan'],p)[0],expected_full,case['id'])
            self.assertEqual(cert_check(case,p)[0],expected_cert,case['id'])
    def test_all_directed_negative_controls(self):
        p=DATA['policy']
        negatives=[c for c in DATA['cases'] if c['id'].startswith('negative-')]
        self.assertEqual(len(negatives),7)
        self.assertEqual(sum(full(c['plan'],p)[0] for c in negatives),3)
        self.assertTrue(all(not cert_check(c,p)[0] for c in negatives))

if __name__=='__main__': unittest.main()
