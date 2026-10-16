import base64
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from agent_review import review, review_native


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.png = self.root / 'frame.png'
        self.pixels = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a9xkAAAAASUVORK5CYII=')
        self.png.write_bytes(self.pixels)
        self.report = self.root / 'report.json'
        self.observation = {'event': 'observation', 'sequence': 2, 'capture_ns': 12,
                            'image': str(self.png)}
        self.rows = [self.observation, {'event': 'independent_evaluation', 'success': True}]

    def write(self, **extra):
        self.report.write_text(json.dumps({'status': 'boundary', 'records': self.rows, **extra}))

    def native_report(self):
        return {'sequence': 7, 'binding_revision': 2, 'capture_ns': 123,
                'native': {'sha256': 'raw-hash', 'capture_started_ns': 123,
                           'artifact': {'path': str(self.png), 'mime_type': 'image/png',
                                        'sha256': hashlib.sha256(self.pixels).hexdigest(),
                                        'source_raw_sha256': 'raw-hash'}}}

    def test_public_dispatch_is_visible_through_research_review(self):
        capture = self.native_report()['native']
        capture['operation_index'] = 3
        payload = {'schema': 'agent-interface/runtime-dispatch-result-v1',
                   'status': 'returned', 'result': {'status': 'execution_failed',
                   'execution': {'error': 'late failure', 'observations': [capture]}}}
        self.report.write_text(json.dumps(payload))
        original = self.report.read_bytes()
        for compact in (False, True):
            row = review(self.report, self.root, compact=compact)
            self.assertEqual(base64.b64decode(row['image']['data']), self.pixels)
            self.assertEqual(row['image_reference']['execution_observation_index'], 0)
            self.assertEqual(row['image_reference']['recorded_capture']['operation_index'], 3)
            self.assertEqual(row['receipt']['report']['result']['status'], 'execution_failed')
        self.png.unlink()
        for compact in (False, True):
            row = review(self.report, self.root, compact=compact)
            self.assertEqual(row['image_status'], 'needs_review')
            self.assertIsNone(row['image'])
            self.assertEqual(row['receipt']['report']['result']['execution']['error'], 'late failure')
        self.assertEqual(self.report.read_bytes(), original)

    def test_native_observation_and_feedback_keep_exact_bytes_and_identity(self):
        observation = self.native_report()
        for report in [observation, {'status': 'needs_review', 'observation': observation,
                                    'task_success': None, 'error': 'focus changed'}]:
            self.report.write_text(json.dumps(report))
            row = review_native(self.report, self.root)
            self.assertEqual(row['receipt']['native_result'], report)
            self.assertEqual(base64.b64decode(row['image']['data']), self.pixels)
            self.assertEqual(row['image_reference']['sequence'], 7)
            self.assertEqual(row['authority'], 'none')

    def test_native_bad_link_or_bytes_never_renders_and_preserves_receipt(self):
        for field in ['source_raw_sha256', 'sha256', 'path']:
            report = self.native_report()
            report['native']['artifact'][field] = 'wrong'
            self.report.write_text(json.dumps(report))
            row = review_native(self.report, self.root)
            self.assertEqual(row['image_status'], 'needs_review')
            self.assertIsNone(row['image'])
            self.assertEqual(row['receipt']['native_result'], report)

    def test_explicit_native_archive_mapping_preserves_original_receipt(self):
        report = self.native_report()
        report['native']['artifact']['path'] = '/retired-host/run/frame.png'
        self.report.write_text(json.dumps(report))
        original = self.report.read_bytes()
        self.assertEqual(review_native(self.report, self.root)['image_status'], 'needs_review')
        mapped = review_native(self.report, self.root, recorded_run_directory='/retired-host/run')
        self.assertEqual(base64.b64decode(mapped['image']['data']), self.pixels)
        self.assertEqual(mapped['receipt']['native_result'], report)
        self.assertEqual(mapped['receipt']['source']['sha256'], hashlib.sha256(original).hexdigest())
        self.assertEqual(self.report.read_bytes(), original)
        self.assertEqual(mapped['archive_mapping']['recorded_image_path'], '/retired-host/run/frame.png')
        self.assertEqual(mapped['archive_mapping']['authority'], 'none')

    def test_archive_mapping_does_not_search_or_accept_escaping_references(self):
        for origin, path in [('/retired-host/run', '/different/run/frame.png'),
                             ('relative', '/retired-host/run/frame.png'),
                             ('/retired-host/run', '/retired-host/run/../frame.png'),
                             ('/retired-host/run', '/retired-host/run/missing/frame.png')]:
            with self.subTest(origin=origin, path=path):
                report = self.native_report()
                report['native']['artifact']['path'] = path
                self.report.write_text(json.dumps(report))
                mapped = review_native(self.report, self.root, recorded_run_directory=origin)
                self.assertEqual(mapped['image_status'], 'needs_review')
                self.assertIsNone(mapped['image'])
                self.assertEqual(mapped['receipt']['native_result'], report)

    def test_native_missing_feedback_image_does_not_use_previous_source(self):
        report = {'status': 'needs_review', 'error': 'BadWindow',
                  'source': self.native_report()}
        self.report.write_text(json.dumps(report))
        row = review_native(self.report, self.root)
        self.assertEqual(row['image_status'], 'no_observation')
        self.assertIsNone(row['image'])
        self.assertEqual(row['receipt']['native_result'], report)

    def test_native_summary_keeps_disagreeing_results_and_bad_image(self):
        from receipt_references import expand_native_receipt
        report = {'status': 'finished', 'evaluation': {'success': True},
                  'action': {'result': {'status': 'completed'},
                             'feedback': {'status': 'needs_review', 'error': 'BadWindow'}},
                  'cleanup': {'status': 'completed', 'tracked_processes_terminal': True,
                              'owner_exit_verified': False, 'descendants_verified': False},
                  'observation': self.native_report()}
        report['observation']['native']['artifact']['sha256'] = 'damaged'
        self.report.write_text(json.dumps(report))
        original = self.report.read_bytes()
        full = review_native(self.report, self.root)
        compact = review_native(self.report, self.root, compact=True)
        self.assertEqual(full['outcome_summary'], {
            'reported_status': 'finished', 'evaluation_success': True,
            'action_status': 'completed', 'feedback_status': 'needs_review',
            'cleanup_status': 'completed', 'cleanup_verification': {
                'tracked_processes_terminal': True, 'owner_exit_verified': False,
                'descendants_verified': False}})
        self.assertEqual(compact['outcome_summary'], full['outcome_summary'])
        self.assertEqual(expand_native_receipt(compact['receipt']), full['receipt'])
        self.assertEqual(full['receipt']['native_result'], report)
        self.assertEqual(full['image_status'], 'needs_review')
        self.assertIsNone(full['image'])
        self.assertEqual(self.report.read_bytes(), original)
        self.assertEqual(full['receipt']['source']['sha256'], hashlib.sha256(original).hexdigest())

    def test_native_summary_never_infers_success_or_uses_history(self):
        for success in [False, None, 0, 1, 'true', {}, []]:
            with self.subTest(success=success):
                report = {'status': 'finished', 'evaluation': {'success': success},
                          'actions': [{'result': {'status': 'completed'}}],
                          'action': [], 'cleanup': {'status': True}}
                self.report.write_text(json.dumps(report))
                row = review_native(self.report, self.root)
                self.assertEqual(row['outcome_summary'], {
                    'reported_status': 'finished',
                    'evaluation_success': False if success is False else None,
                    'action_status': None, 'feedback_status': None, 'cleanup_status': None})
                self.assertEqual(row['image_status'], 'no_observation')
        for report in [{}, {'status': [], 'evaluation': [], 'action': {'result': None}}]:
            self.report.write_text(json.dumps(report))
            self.assertTrue(all(value is None for value in
                                review_native(self.report, self.root)['outcome_summary'].values()))

    def test_cleanup_verification_requires_explicit_booleans(self):
        from agent_review import native_outcome_summary
        for value in (None, 0, 1, 'true', [], {}):
            summary = native_outcome_summary({'cleanup': {
                'status': 'completed', 'tracked_processes_terminal': value}})
            self.assertEqual(summary['cleanup_verification'], {
                'tracked_processes_terminal': None, 'owner_exit_verified': None,
                'descendants_verified': None})
        for cleanup in (None, [], {}, {'status': 'completed'}):
            self.assertNotIn('cleanup_verification', native_outcome_summary({'cleanup': cleanup}))

    def test_native_target_refusal_is_visible_without_claiming_action_success(self):
        from receipt_references import expand_native_receipt
        refusal = {'reason': 'visually_flat_source_region', 'input_dispatched': False,
                   'action_attempted': False, 'finish_after_applied': False}
        report = {'status': 'boundary', 'target_refusal': refusal,
                  'observation': self.native_report()}
        self.report.write_text(json.dumps(report))
        for compact in (False, True):
            row = review_native(self.report, self.root, compact=compact)
            summary = row['outcome_summary']
            self.assertEqual(summary['target_refusal'], refusal)
            self.assertEqual(summary['reported_status'], 'boundary')
            self.assertIsNone(summary['action_status'])
            self.assertIsNone(summary['evaluation_success'])
            self.assertEqual(base64.b64decode(row['image']['data']), self.pixels)
            receipt = expand_native_receipt(row['receipt']) if compact else row['receipt']
            self.assertEqual(receipt['native_result'], report)

    def test_native_refusal_projection_does_not_coerce_or_infer_input_safety(self):
        from agent_review import native_outcome_summary
        for value in (None, 0, 1, 'false', [], {}):
            summary = native_outcome_summary({'target_refusal': {
                'reason': [], 'input_dispatched': value,
                'action_attempted': value, 'finish_after_applied': value}})
            self.assertTrue(all(v is None for v in summary['target_refusal'].values()))
        for value in (True, False):
            summary = native_outcome_summary({'target_refusal': {'input_dispatched': value}})
            self.assertIs(summary['target_refusal']['input_dispatched'], value)
        self.assertNotIn('target_refusal', native_outcome_summary({'target_refusal': 'invalid'}))
        self.assertNotIn('target_refusal', native_outcome_summary({'actions': []}))

    def test_image_bytes_and_full_result_share_one_response(self):
        self.write()
        original = self.report.read_bytes()
        result = review(self.report, self.root)
        self.assertEqual(base64.b64decode(result['image']['data']), self.pixels)
        self.assertEqual(result['receipt']['events'], [self.rows[-1]])
        self.assertEqual(result['receipt']['source']['sha256'], hashlib.sha256(original).hexdigest())
        self.assertEqual(self.report.read_bytes(), original)

    def test_mutated_image_preserves_result_without_rendering(self):
        self.write(image={'status': 'image', 'sequence': 2, 'capture_ns': 12,
                          'path': str(self.png), 'sha256': 'wrong'})
        result = review(self.report, self.root)
        self.assertIsNone(result['image'])
        self.assertIn('sha256', result['image_error'])
        self.assertTrue(result['receipt']['events'][0]['success'])

    def test_conflicting_latest_image_is_not_silently_selected(self):
        self.rows.append({**self.observation, 'capture_ns': 13})
        self.write()
        result = review(self.report, self.root)
        self.assertIsNone(result['image'])
        self.assertEqual(len(result['receipt']['latest_observations']), 2)

    def test_missing_latest_does_not_fall_back_to_older_image(self):
        self.rows.append({**self.observation, 'sequence': 3, 'image': str(self.root/'missing.png')})
        self.write()
        result = review(self.report, self.root)
        self.assertIsNone(result['image'])
        self.assertEqual(result['image_status'], 'needs_review')

    def test_no_observation_does_not_show_pre_action_source(self):
        self.rows = [{'event': 'rejected', 'reason': 'stale'}]
        self.write(source_image={'path': str(self.png)})
        result = review(self.report, self.root)
        self.assertIsNone(result['image'])
        self.assertEqual(result['image_status'], 'no_observation')
        self.assertEqual(result['receipt']['events'], self.rows)

    def test_compact_review_preserves_image_and_expands_to_full_receipt(self):
        from receipt_references import expand_receipt
        self.write(outcome={'evidence': self.rows[-1]})
        full = review(self.report, self.root)
        compact = review(self.report, self.root, compact=True)
        self.assertEqual(compact['image'], full['image'])
        self.assertEqual(compact['image_reference'], full['image_reference'])
        self.assertEqual(expand_receipt(compact['receipt']), full['receipt'])


if __name__ == '__main__':
    unittest.main()
