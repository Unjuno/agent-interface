"""Study lifecycle/source contract tests without GUI/model side effects."""
import importlib
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
        config = self.root/'plan.json'
        config.write_text(json.dumps(plan))
        with self.assertRaises(ValueError):
            self.module.run(config, self.root/'out', self.root/'exchange')
        self.assertFalse((self.root/'out').exists())
        self.assertFalse((self.root/'exchange').exists())


if __name__ == '__main__':
    unittest.main()
