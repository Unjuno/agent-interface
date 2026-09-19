import copy
import unittest
from receipt_references import compact_receipt, expand_receipt


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


if __name__ == '__main__':
    unittest.main()
