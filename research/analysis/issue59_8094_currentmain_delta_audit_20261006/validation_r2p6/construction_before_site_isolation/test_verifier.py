"""Construction regressions: same inputs and actual processes for v1 and v2."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from fixture import build, corpus

HERE = Path(__file__).resolve().parent
class VerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='ai59-verifier-unit-')
        cls.root = Path(cls.temp.name)
        cls.repo, base = build(cls.root)
        cls.cases = corpus(base)
        cls.subject = Path(os.environ.get('VERIFIER', str(HERE/'verify_v2.py')))
    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()
    def test_source_table_contract(self):
        for case in self.cases:
            for opt in (False, True):
                with self.subTest(case=case['name'], optimized=opt):
                    folder = self.root / (case['name']+str(opt)); folder.mkdir()
                    subject = folder/'subject.py'; shutil.copyfile(self.subject, subject)
                    (folder/'RESULT.json').write_text(case['input'])
                    cmd = [sys.executable,'-I','-B']+(['-O'] if opt else [])+[str(subject),'--repo',str(self.repo),'--result',str(folder/'RESULT.json')]
                    p = subprocess.run(cmd, capture_output=True, timeout=5)
                    self.assertEqual(p.returncode==0, case['expected_accept'], p.stdout.decode(errors='replace'))

if __name__=='__main__': unittest.main()
