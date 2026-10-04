"""Study lifecycle/source contract tests without GUI/model side effects."""
import importlib
import hashlib
import json
from pathlib import Path
import tempfile
import unittest


class StudyLifecycleTests(unittest.TestCase):
    def setUp(self):
        try:
            self.module = importlib.import_module('paired_study')
        except ImportError as error:
            self.fail('Actual paired study entry absent: '+str(error))
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_source_mismatch_stops_before_owned_app_or_exchange_directory(self):
        source = self.root/'source.py'
        source.write_bytes(b'changed')
        plan = dict(schema='a15-live-paired-study-v1', allocation='construction-only',
            source_sha256={str(source):'0'*64}, rows=[dict(id='pair-000', wanted='vkc',
                target='kc', decoy='', focus_drift=False)],
            prompt='Construction only', response_timeout_seconds=10)
        root = Path(self.module.__file__).resolve().parent
        for name in ('paired_study.py','live_pair.py','live_app.py','task_session.py',
                     'task_guard.py','file_exchange.py','host_bridge.py',
                     'model_contract.py','construction_x11.py'):
            path = root/name
            plan['source_sha256'][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        config = self.root/'plan.json'
        config.write_text(json.dumps(plan))
        with self.assertRaisesRegex(ValueError, 'METHOD_STOP_SOURCE_CHANGED'):
            self.module.run(config, self.root/'out', self.root/'exchange')
        self.assertFalse((self.root/'out').exists())
        self.assertFalse((self.root/'exchange').exists())

    def test_omitted_local_sources_stop_before_output_or_exchange_creation(self):
        source = self.root/'listed.py'
        source.write_bytes(b'valid listed bytes')
        plan = dict(schema='a15-live-paired-study-v1', allocation='construction-only',
            source_sha256={str(source):hashlib.sha256(source.read_bytes()).hexdigest()},
            rows=[dict(id='pair-000', wanted='vkc', target='kc', decoy='', focus_drift=False)],
            prompt='Construction only', response_timeout_seconds=10)
        config = self.root/'plan.json'
        config.write_text(json.dumps(plan))
        with self.assertRaisesRegex(ValueError, 'METHOD_STOP_LOCAL_SOURCE_UNCOVERED'):
            self.module.run(config, self.root/'out', self.root/'exchange')
        self.assertFalse((self.root/'out').exists())
        self.assertFalse((self.root/'exchange').exists())


if __name__ == '__main__':
    unittest.main()
