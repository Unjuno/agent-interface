import unittest
from candidate import classify
from corpus import build_rows

class ContractTests(unittest.TestCase):
    def test_corpus_size(self): self.assertEqual(len(build_rows()),144)
    def test_stale_unknown(self):
        r=next(x for x in build_rows() if x['freshness']=='STALE')
        self.assertEqual(classify(r)['label'],'FAILED_UNKNOWN')
    def test_authority_never_granted(self):
        self.assertTrue(all(classify(r)['authority_granted'] is False for r in build_rows()))
    def test_blocked_retry_only_when_valid(self):
        xs=[r for r in build_rows() if r['family']=='BLOCKED' and r['freshness']=='CURRENT' and r['completeness']=='COMPLETE']
        self.assertEqual({classify(r)['identical_retry_allowed'] for r in xs},{False,True})
if __name__=='__main__': unittest.main()
