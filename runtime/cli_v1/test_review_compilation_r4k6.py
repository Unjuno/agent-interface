"""Read-only mixed-compilation diagnostics; no backend, display, or input."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from runtime.cli_v1.review import review_bytes
from runtime.cli_v1.receipt_references import expand_receipt
from runtime.core_v1.sequence import expand_text_gaps


def example(partial=False):
    ops = [
        {'op': 'focus', 'target': 'entry'},
        {'op': 'text', 'text': 'abcd', 'gap_ms': 5},
        {'op': 'key_chord', 'keys': ['BackSpace'], 'repeat': 2},
        {'op': 'text', 'text': 'xy', 'gap_ms': 5},
        {'op': 'observe', 'x': 0, 'y': 0, 'width': 1, 'height': 1},
        {'op': 'release_all'},
    ]
    _, mapping = expand_text_gaps(ops)
    result = {'status': 'refused', 'error': 'INVALID_PROGRAM',
              'detail': 'observe w must be int',
              'detail_source': 'program_validation',
              'validation_operation_index': 13}
    if partial:
        result = {'status': 'execution_failed', 'error': 'BACKEND_EXECUTION_FAILED',
                  'recovery_required': False, 'execution': {
                      'completed_ops': list(range(13)), 'failed_op': 13,
                      'failed_op_effect': 'unknown; may have emitted partial input',
                      'observations': [], 'releases': [
                          {'verified': True, 'keys_down': [], 'buttons_down': []}]}}
    return {'schema': 'agent-interface/runtime-dispatch-result-v1',
            'status': 'returned', 'result': result, 'compilation': {
                'kind': 'bounded_text_gap', 'source_program': {'ops': ops},
                'operation_sources': mapping}}


def view(report, root, mode=0):
    return review_bytes(json.dumps(report).encode(), root,
                        compact=mode > 0, report_refs=mode == 2)


class ReviewCompilationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_static_position_is_source_not_expanded_position(self):
        report = example()
        for mode in range(3):
            summary = view(report, self.root, mode)['outcome_summary']
            self.assertEqual(summary['validation_operation_index'], 13)
            self.assertEqual(summary['validation_source_operation'],
                             {'source_operation_index': 4, 'expanded_occurrence': 1})
            self.assertEqual(summary['execution_status'], 'refused')
            self.assertIsNone(summary['input_release_verified'])

    def test_partial_prefix_and_uncertainty_survive(self):
        report = example(True)
        result = view(report, self.root, 2)
        summary = result['outcome_summary']
        self.assertEqual(summary['failed_operation_index'], 13)
        self.assertEqual(summary['failed_source_operation']['source_operation_index'], 4)
        self.assertEqual(summary['failed_operation_effect'],
                         report['result']['execution']['failed_op_effect'])
        self.assertEqual(expand_receipt(result['receipt'])['report'], report)
        self.assertEqual(summary['execution_status'], 'execution_failed')
        self.assertNotIn('task_success', summary)

    def test_inconsistent_and_boolean_maps_do_not_supply_locations(self):
        for value in (0, True):
            report = example()
            report['compilation']['operation_sources'][13]['source_operation_index'] = value
            for mode in range(3):
                summary = view(report, self.root, mode)['outcome_summary']
                self.assertEqual(summary['validation_operation_index'], 13)
                self.assertIsNone(summary['validation_source_operation'])

    def test_boolean_failed_index_is_unknown(self):
        report = example(True)
        report['result']['execution']['failed_op'] = True
        summary = view(report, self.root)['outcome_summary']
        self.assertIsNone(summary['failed_operation_index'])
        self.assertIsNone(summary['failed_source_operation'])

    def test_absent_release_is_not_verified(self):
        report = example(True)
        report['result']['execution']['releases'] = []
        self.assertIsNone(view(report, self.root)['outcome_summary']['input_release_verified'])

    def test_later_success_does_not_hide_failed_release(self):
        report = example(True)
        report['result']['execution']['releases'].insert(0,
            {'verified': False, 'keys_down': ['a'], 'buttons_down': []})
        self.assertIs(view(report, self.root)['outcome_summary']['input_release_verified'], False)

    def test_missing_image_retains_diagnostics(self):
        report = example(True)
        report['result']['execution']['observations'] = [{
            'sha256': '0' * 64, 'artifact': {'mime_type': 'image/png',
            'source_raw_sha256': '0' * 64, 'sha256': '1' * 64,
            'path': 'unavailable.png'}}]
        for mode in range(3):
            result = view(report, self.root, mode)
            self.assertEqual(result['image_status'], 'needs_review')
            self.assertIsNone(result['image'])
            self.assertEqual(result['outcome_summary']['execution_status'], 'execution_failed')
            self.assertEqual(result['outcome_summary']['failed_source_operation']['source_operation_index'], 4)

    def test_projection_roundtrip_and_input_immutability(self):
        for partial in (False, True):
            report = example(partial)
            before = deepcopy(report)
            for mode in range(3):
                result = view(report, self.root, mode)
                self.assertEqual(expand_receipt(result['receipt'])['report'], report)
                self.assertEqual(result['authority'], 'none')
                self.assertEqual(result['receipt']['authority'], 'none')
            self.assertEqual(report, before)
        self.assertEqual(list(self.root.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
