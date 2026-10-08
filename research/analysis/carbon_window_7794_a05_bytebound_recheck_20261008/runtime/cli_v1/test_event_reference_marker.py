"""A declared event reference has one canonical integer marker."""
from copy import deepcopy
import json
import unittest

from runtime.cli_v1.receipt_references import compact_receipt, expand_receipt


def view(number, marker, path='/report/value'):
    value = {'event_ref': marker}
    return {'schema': 'agent-interface/receipt-view-v2-event-refs',
            'events': [{'kind': 'zero'}, {'kind': 'one'}],
            'report': value if path == '/report' else {'value': value},
            'event_references': {path: number}, 'reference_scope': 'local'}


def identity(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


class EventReferenceMarkerTests(unittest.TestCase):
    def test_boolean_markers_do_not_alias_integer_indices(self):
        for number, marker in ((0, False), (1, True)):
            with self.subTest(number=number, marker=marker):
                value = view(number, marker)
                before = identity(value)
                with self.assertRaises(ValueError):
                    expand_receipt(value)
                self.assertEqual(identity(value), before)

    def test_float_markers_do_not_alias_integer_indices(self):
        for number, marker in ((0, 0.0), (0, -0.0), (1, 1.0)):
            with self.subTest(number=number, marker=marker):
                value = view(number, marker)
                before = identity(value)
                with self.assertRaises(ValueError):
                    expand_receipt(value)
                self.assertEqual(identity(value), before)

    def test_canonical_integer_markers_preserve_nested_and_root_locations(self):
        for number in (0, 1):
            for path in ('/report/value', '/report'):
                with self.subTest(number=number, path=path):
                    value = view(number, number, path)
                    before = identity(value)
                    result = expand_receipt(value)
                    expected = deepcopy(value['events'][number])
                    self.assertEqual(result['report'], expected if path == '/report' else {'value': expected})
                    self.assertEqual(identity(value), before)
                    self.assertEqual(result['schema'], 'agent-interface/receipt-view-v1')

    def test_unlisted_reference_shaped_values_remain_literal(self):
        for marker in (False, True, 0.0, -0.0, 1.0):
            with self.subTest(marker=marker):
                value = view(0, marker)
                value['event_references'] = {}
                result = expand_receipt(value)
                self.assertEqual(identity(result['report']), identity(value['report']))

    def test_noncanonical_declared_indices_still_refuse(self):
        for number in (False, True, 0.0, 1.0, '0', None):
            with self.subTest(number=number):
                with self.assertRaises(ValueError):
                    expand_receipt(view(number, number))

    def test_marker_shape_mismatch_still_refuses(self):
        for marker in ({}, {'event_ref': 0, 'extra': True}, [], 0, None):
            with self.subTest(marker=marker):
                value = view(0, 0)
                value['report']['value'] = marker
                with self.assertRaises(ValueError):
                    expand_receipt(value)

    def test_compactor_round_trip_preserves_literal_marker_number_types(self):
        events = [{'event_ref': False}, {'event_ref': 0}, {'event_ref': 0.0}]
        value = {'schema': 'agent-interface/receipt-view-v1', 'events': events,
                 'report': {'rows': deepcopy(events)}}
        before = identity(value)
        self.assertEqual(identity(expand_receipt(compact_receipt(value))), before)
        self.assertEqual(identity(value), before)


if __name__ == '__main__':
    unittest.main()
