import copy
import unittest
from receipt_references import compact_receipt, expand_receipt, compact_native_receipt, expand_native_receipt


class ReferenceTests(unittest.TestCase):
    def view(self, report, events):
        return {'schema': 'agent-interface/receipt-view-v1', 'report': report,
                'events': events, 'latest_observations': [{'sequence': 4, 'image': 'kept'}],
                'source': {'path': 'raw.json', 'sha256': 'retained'}, 'omitted_from_view': 2}

    def test_roundtrip_keeps_every_event_and_all_metadata(self):
        event = {'event': 'independent_evaluation', 'success': False, 'reason': 'mismatch'}
        original = self.view({'outcome': {'evidence': event}, 'drain': {'rows': [event]}}, [event])
        before = copy.deepcopy(original)
        compact = compact_receipt(original)
        self.assertEqual(compact['report']['outcome']['evidence'], {'event_ref': 0})
        self.assertEqual(compact['events'], [event])
        self.assertEqual(expand_receipt(compact), original)
        self.assertEqual(original, before)

    def test_near_duplicates_and_unknown_fields_are_not_merged(self):
        event = {'event': 'new_critical_event', 'value': 1}
        different = {'event': 'new_critical_event', 'value': True}
        original = self.view({'new_field': different, 'extra': {'event_ref': 0}}, [event])
        compact = compact_receipt(original)
        self.assertEqual(compact['event_references'], {})
        self.assertEqual(expand_receipt(compact), original)

    def test_pointer_escaping_and_literal_reference_shaped_data(self):
        event = {'event': 'unknown', 'payload': {'event_ref': 99}}
        original = self.view({'a/b~': [event], 'literal': {'event_ref': 0}}, [event])
        compact = compact_receipt(original)
        self.assertIn('/report/a~1b~0/0', compact['event_references'])
        self.assertEqual(expand_receipt(compact), original)

    def test_full_report_match_and_invalid_reference(self):
        event = {'event': 'future', 'status': 'unknown'}
        original = self.view(event, [event])
        compact = compact_receipt(original)
        self.assertEqual(expand_receipt(compact), original)
        compact['event_references']['/report'] = -1
        with self.assertRaises(ValueError):
            expand_receipt(compact)


class NativeReferenceTests(unittest.TestCase):
    def test_exact_observation_roundtrip_preserves_errors_and_literal_markers(self):
        observation = {'sequence': 7, 'native': {'sha256': 'a'*64, 'payload': 'x'*1000}}
        view = {'source': {'sha256': 'source'}, 'native_result': {
            'observation': observation, 'action': {'window/review~': [observation],
                'feedback': {'status': 'needs_review', 'error': 'BadWindow'},
                'literal': {'observation_ref': '/native_result/observation'}},
            'task_success': None}}
        before = copy.deepcopy(view)
        compact = compact_native_receipt(view)
        self.assertEqual(compact['observation_references'], ['/native_result/action/window~1review~0/0'])
        self.assertEqual(compact['native_result']['observation'], observation)
        self.assertEqual(expand_native_receipt(compact), view)
        self.assertEqual(view, before)

    def test_near_duplicates_and_small_reports_remain_unchanged(self):
        for view in [
            {'native_result': {'status': 'finished', 'evaluation': {'success': False}}},
            {'native_result': {'observation': {'sequence': 1, 'native': {}},
                               'copy': {'sequence': 1, 'native': {}}}},
            {'native_result': {'observation': {'sequence': 1, 'native': {'padding': 'x'*1000}},
                               'copy': {'sequence': True, 'native': {'padding': 'x'*1000}}}}]:
            self.assertEqual(compact_native_receipt(view), view)
            self.assertEqual(expand_native_receipt(compact_native_receipt(view)), view)

    def test_invalid_reference_cannot_replace_canonical_source(self):
        observation = {'native': {'padding': 'x'*1000}}
        compact = compact_native_receipt({'native_result': {'observation': observation, 'copy': observation}})
        compact['observation_references'] = ['/native_result/observation']
        with self.assertRaises(ValueError):
            expand_native_receipt(compact)


if __name__ == '__main__':
    unittest.main()
