import unittest
from effect_predicate import visible_row_predicate

class VisibleEffectContract(unittest.TestCase):
    def test_unavailable_is_not_effect_failure(self):
        self.assertEqual(visible_row_predicate(None,['23','31','713']),'unknown')
    def test_readable_wrong_value_is_failure(self):
        self.assertIs(visible_row_predicate(['32','37','1184'],['31','37','1147']),False)
    def test_readable_expected_values_are_positive(self):
        self.assertIs(visible_row_predicate(['23','31','713'],['23','31','713']),True)
    def test_partial_or_malformed_values_are_unavailable(self):
        for value in ([],['23','31'],['23','31',None],['23','31',''],True,['２３','31','713']):
            self.assertEqual(visible_row_predicate(value,['23','31','713']),'unknown')

if __name__=='__main__':unittest.main(verbosity=2)
