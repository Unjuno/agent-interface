import unittest
from research.live_control.calc_ocr_pair_cue_v1 import classify_pair

def tsv(text,confidence='95',level='5'):
    return 'level\tconf\ttext\n'+level+'\t'+confidence+'\t'+text+'\n'

class PairCueTests(unittest.TestCase):
    def test_expected_values_are_explicit_per_call(self):
        self.assertEqual(classify_pair(tsv('641'),tsv('283'),expected=('641','283')),'filled')
        self.assertEqual(classify_pair(tsv('641'),tsv('283'),expected=('329','517')),'wrong')
        self.assertEqual(classify_pair(tsv('329'),tsv('517'),expected=('329','517')),'filled')
    def test_unknown_ocr_fails_closed(self):
        for first in [tsv('641','89.99'),tsv('641','nan'),tsv('641','95','4'),tsv('64a'),tsv('641')+tsv('641'),'',None]:
            with self.subTest(first=first):
                self.assertEqual(classify_pair(first,tsv('283'),expected=('641','283')),'unknown')
    def test_mismatch_is_wrong(self):
        self.assertEqual(classify_pair(tsv('641'),tsv('284'),expected=('641','283')),'wrong')
    def test_invalid_expectations_are_rejected(self):
        for expected in [None,('641',),('641',283),('','283'),('６４１','283'),('64 1','283'),['641','283']]:
            with self.subTest(expected=expected):
                with self.assertRaises(ValueError): classify_pair(tsv('641'),tsv('283'),expected=expected)
if __name__=='__main__': unittest.main()
