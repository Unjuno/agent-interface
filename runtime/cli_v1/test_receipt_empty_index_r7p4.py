"""Pure current-module regressions for the empty event-index fast path.

Run directly; no CLI package/backend is imported. RECEIPT_MODULE_PATH selects
an explicit source file for before/after qualification, not a runtime option.
"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest

SOURCE = Path(os.environ.get('RECEIPT_MODULE_PATH',
    str(Path(__file__).with_name('receipt_references.py'))))
spec = importlib.util.spec_from_file_location('receipt_subject_r7p4', SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def view(report, events=None):
    return {'schema': 'agent-interface/receipt-view-v1', 'authority': 'none',
            'report': report, 'events': [] if events is None else events,
            'source': {'kind': 'received_bytes', 'raw_report': copy.deepcopy(report)}}


class EmptyIndexTests(unittest.TestCase):
    def test_empty_index_encodes_root_once_not_every_descendant(self):
        data = view({'a': {'b': [{'c': {'d': 'leaf'}}]}})
        calls = []
        def profile(frame, event, arg):
            if event == 'call' and frame.f_code is m._encoded.__code__:
                calls.append(None)
        previous = sys.getprofile()
        try:
            sys.setprofile(profile)
            result = m.compact_receipt(data)
        finally:
            sys.setprofile(previous)
        self.assertEqual(result['event_references'], {})
        self.assertEqual(len(calls), 1)

    def test_copy_is_independent_of_input(self):
        data = view({'tree': {'leaf': [1, 2]}})
        original = copy.deepcopy(data)
        result = m.compact_receipt(data)
        result['report']['tree']['leaf'].append(3)
        self.assertEqual(data, original)
        self.assertEqual(result['source']['raw_report'], original['report'])

    def test_nonfinite_values_still_refuse(self):
        for value in (float('nan'), float('inf'), -float('inf')):
            with self.subTest(value=repr(value)), self.assertRaises(ValueError):
                m.compact_receipt(view({'outer': [{'value': value}]}))

    def test_nonjson_value_still_refuses(self):
        with self.assertRaises(TypeError):
            m.compact_receipt(view({'outer': {'value': {1, 2}}}))

    def test_event_roundtrip_keeps_failed_release_and_unknown_effect(self):
        event = {'event': 'release_failed', 'verified': False, 'reason': 'x' * 900}
        data = view({'event_copy': copy.deepcopy(event), 'recovery_required': True,
                     'task_success': None, 'failed_op_effect': 'unknown'}, [event])
        compact = m.compact_receipt(data)
        self.assertTrue(compact['event_references'])
        self.assertEqual(m.expand_receipt(compact), data)

    def test_report_reference_selection_stays_reversible(self):
        data = view({'payload': 'abc' * 900, 'task_success': None})
        result = m.compact_receipt(data, report_refs=True)
        self.assertEqual(result['schema'], m.REPORT_REF)
        self.assertEqual(m.expand_receipt(result), data)

    def test_escaped_paths_roundtrip(self):
        event = {'event': 'warning', 'text': '日本語' * 80}
        data = view({'a~/': {'~1': [copy.deepcopy(event)]}}, [event])
        self.assertEqual(m.expand_receipt(m.compact_receipt(data)), data)

    def test_malformed_array_aliases_still_refuse(self):
        event = {'event': 'warning', 'text': 'x' * 300}
        base = m.compact_receipt(view({'items': [copy.deepcopy(event)]}, [event]))
        for pointer in ('/report/items/00', '/report/items/-1', '/report/items/+0',
                        '/report/items/0~2'):
            bad = copy.deepcopy(base)
            bad['event_references'] = {pointer: 0}
            with self.subTest(pointer=pointer), self.assertRaises(ValueError):
                m.expand_receipt(bad)

    def test_literal_marker_is_not_resolved(self):
        data = view({'literal': {'event_ref': 0}, 'report_ref': '/source/raw_report'})
        self.assertEqual(m.expand_receipt(m.compact_receipt(data)), data)

    def test_native_multiple_roundtrip(self):
        a = {'sequence': 1, 'native': {'payload': 'a' * 1200}}
        b = {'sequence': 2, 'native': {'payload': 'b' * 1200}}
        data = {'native_result': {'observation': a, 'others': [a, b, b]},
                'recovery_required': True, 'task_success': None}
        self.assertEqual(m.expand_native_receipt(m.compact_native_receipt(data)), data)

    def test_guarded_observation_roundtrip(self):
        native = {'pixels': 'x' * 1800}
        data = {'operation': 'guarded_observe', 'status': 'observed',
                'image_status': 'image', 'source': {'native': native, 'observation_id': 'o1'},
                'observation_report': {'status': 'returned', 'observation_id': 'o1',
                                       'observation': copy.deepcopy(native)}}
        result = m.compact_guarded_observation(data)
        self.assertIn('reference_schema', result)
        self.assertEqual(m.expand_guarded_observation(result), data)

    def test_guarded_feedback_roundtrip(self):
        source = {'native': {'pixels': 'z' * 2000}, 'observation_id': 'o2'}
        data = {'operation': 'guarded_input', 'status': 'completed',
                'task_success': None, 'replay_allowed': False, 'image_status': 'image',
                'feedback_status': 'cue_returned', 'source': source,
                'feedback': {'status': 'matched', 'task_success': None,
                    'authority_granted': False, 'input_dispatched': False,
                    'expected_title': 'Fixture', 'title': 'Fixture', 'after_title': 'Fixture',
                    'observation': copy.deepcopy(source)},
                'result': {'status': 'completed', 'recovery_required': False,
                    'execution': {'releases': [{'verified': True, 'keys_down': [], 'buttons_down': []}]}},
                'session': {'recovery_required': False, 'review_required': False},
                'observation_report': {'status': 'returned', 'observation_id': 'o2',
                                       'observation': copy.deepcopy(source['native'])}}
        result = m.compact_guarded_observation(data)
        self.assertIn('reference_schema', result)
        self.assertEqual(m.expand_guarded_observation(result), data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
