import unittest
from primary_usage_projection import project
from test_primary_usage_projection import call, output, usage

class CrossWindow(unittest.TestCase):
    def selection(self):
        return [dict(name=n,begin_call_id=n,end_call_id=n) for n in ('a','b')]
    def test_same_response_in_distinct_windows_is_ambiguous(self):
        with self.assertRaises(ValueError):
            project([call('a'),usage('same'),output('a'),call('b'),usage('same'),output('b')],self.selection())
    def test_conflicting_response_across_windows_is_refused(self):
        with self.assertRaises(ValueError):
            project([call('a'),usage('same'),output('a'),call('b'),usage('same',101),output('b')],self.selection())
    def test_distinct_response_windows_remain_accounted(self):
        result=project([call('a'),usage('one'),output('a'),call('b'),usage('two'),output('b')],self.selection())
        self.assertEqual([w['totals']['total_tokens'] for w in result['windows']],[120,120])
