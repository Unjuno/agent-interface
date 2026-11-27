import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from launch_recorded import launch_recorded

class ArchivedLauncherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).resolve().parents[3]
        data=subprocess.check_output(['git','show',
            'd69368d47f798dc011aa3264f1b0004a0829be04:research/integration/wslc_calc_three_arm_reverse_20261101/raw.zip'],
            cwd=root)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            cls.source=archive.read('ep02/launch.py')
        if hashlib.sha256(cls.source).hexdigest()!='feaf6b0dcc0f49bb031cdffa0a9d1437a33bb88f57435924d103911039cab2cf':
            raise RuntimeError('unexpected archived source')

    def test_early_failure_retains_records_before_any_process(self):
        for case,error in [('missing_conditions',FileNotFoundError),('hash_mismatch',RuntimeError)]:
            with self.subTest(case=case),tempfile.TemporaryDirectory() as td:
                root=Path(td); launcher=root/'launch.py'; launcher.write_bytes(self.source)
                if case=='hash_mismatch':
                    (root/'payload').write_text('changed')
                    (root/'conditions.json').write_text(json.dumps({'input_sha256':{'payload':'0'*64}}))
                attempt=root/'outer'
                with patch('subprocess.Popen',side_effect=AssertionError('must not launch')) as popen:
                    with self.assertRaises(error): launch_recorded(launcher,attempt)
                    popen.assert_not_called()
                start=json.loads((attempt/'attempt-start.json').read_text())
                terminal=json.loads((attempt/'attempt-terminal.json').read_text())
                self.assertEqual(terminal['error_type'],error.__name__)
                self.assertGreaterEqual(terminal['ended_ns'],start['started_ns'])
                self.assertIsNone(terminal['usage'])
                self.assertFalse(terminal['replay_allowed'])
                self.assertFalse((root/'launcher-result.json').exists())
