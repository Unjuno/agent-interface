"""Saved-data scoring must not trust producer SAVE_DISPATCHED claims."""
import hashlib
import importlib
import json
from pathlib import Path
import tempfile
import unittest


class FileAuditTests(unittest.TestCase):
    def setUp(self):
        try:
            self.module = importlib.import_module('file_audit')
        except ImportError as error:
            self.fail('Independent saved-file scorer absent: '+str(error))
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ready = dict(pid=21, token='private-arm')

    def fixture(self, text='vnr', decoy='', events=None):
        blob = json.dumps(dict(schema='issue5260-a15-task-file-v1',
                              pid=21, token='private-arm', text=text)).encode()
        (self.root/'task_result.json').write_bytes(blob)
        app = dict(pid=21, token='private-arm', target=text, decoy=decoy,
            started_ns=10, ended_ns=100, events=events or [],
            saves=[dict(status='saved', bytes=len(blob),
                        sha256=hashlib.sha256(blob).hexdigest(), started_ns=40, completed_ns=50)])
        (self.root/'app_result.json').write_text(json.dumps(app))
        (self.root/'ready.json').write_text(json.dumps(self.ready))

    def test_exact_actual_file_scores_completed_without_producer_outcome(self):
        self.fixture()
        self.assertEqual(self.module.score_arm(self.root, wanted='vnr', initial_decoy='')['quality'],
                         'EXACT_FILE')

    def test_wrong_saved_text_is_wrong_file_not_completion(self):
        self.fixture(text='nr')
        self.assertEqual(self.module.score_arm(self.root, wanted='vnr', initial_decoy='')['quality'],
                         'WRONG_FILE')

    def test_tampered_file_is_custody_error_even_with_desired_text(self):
        self.fixture()
        (self.root/'task_result.json').write_bytes((self.root/'task_result.json').read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError, 'FILE_RECEIPT_MISMATCH'):
            self.module.score_arm(self.root, wanted='vnr', initial_decoy='')

    def test_wrong_recipient_key_is_detected_even_if_decoy_text_unchanged(self):
        self.fixture(events=[dict(widget='decoy', kind='KeyPress', ns=30)])
        result = self.module.score_arm(self.root, wanted='vnr', initial_decoy='')
        self.assertEqual(result['wrong_recipient_events'], 1)
        self.assertEqual(result['quality'], 'WRONG_RECIPIENT_INPUT')

    def test_no_file_and_no_save_is_unfinished_not_completion(self):
        self.fixture()
        (self.root/'task_result.json').unlink()
        app = json.loads((self.root/'app_result.json').read_bytes())
        app['saves'] = []
        (self.root/'app_result.json').write_text(json.dumps(app))
        self.assertEqual(self.module.score_arm(self.root, wanted='vnr', initial_decoy='')['quality'],
                         'UNFINISHED_NO_FILE')

    def test_malformed_identity_or_text_cannot_score_exact_even_with_matching_receipt(self):
        for field, value in [('token',None), ('pid',True), ('text',None)]:
            with self.subTest(field=field):
                self.fixture()
                ready = json.loads((self.root/'ready.json').read_bytes())
                app = json.loads((self.root/'app_result.json').read_bytes())
                saved = json.loads((self.root/'task_result.json').read_bytes())
                saved[field] = value
                if field == 'text':
                    app['target'] = value
                else:
                    app[field] = ready[field] = value
                blob = json.dumps(saved).encode()
                app['saves'][0].update(bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest())
                (self.root/'ready.json').write_text(json.dumps(ready))
                (self.root/'app_result.json').write_text(json.dumps(app))
                (self.root/'task_result.json').write_bytes(blob)
                with self.assertRaisesRegex(ValueError, 'SCHEMA_INVALID'):
                    self.module.score_arm(self.root, wanted=None if field=='text' else 'vnr',
                                          initial_decoy='')

    def test_malformed_event_kind_is_schema_error_not_exact_file(self):
        self.fixture(events=[dict(widget='target',kind='unknown',ns=30)])
        with self.assertRaisesRegex(ValueError, 'SCHEMA_INVALID'):
            self.module.score_arm(self.root,wanted='vnr',initial_decoy='')


if __name__ == '__main__':
    unittest.main()
