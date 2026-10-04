import unittest
import subprocess
import sys
import tempfile
from pathlib import Path
from admission import require_formal

class Admission(unittest.TestCase):
    def test_formal_is_not_admitted_from_failed_readiness(self):
        with self.assertRaisesRegex(RuntimeError, 'STOP_READINESS_SOURCE_EXPOSURE'):
            require_formal()

    def test_all_formal_entrypoints_refuse_before_outputs(self):
        here = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory(prefix='phase-a02-admission-') as temporary:
            for script, args in (
                ('producer.py', ['--formal']),
                ('runner.py', ['--mode','formal','--guest-source','/not-a-source','--guest-output','/not-an-output']),
                ('auditor.py', ['--raw','/not-raw','--fixture',str(here/'fixture.json')])):
                output = Path(temporary) / script
                r = subprocess.run([sys.executable,'-B',str(here/script),*args,'--out',str(output)],
                                   capture_output=True,text=True)
                self.assertEqual(r.returncode,1,script)
                self.assertIn('STOP_READINESS_SOURCE_EXPOSURE',r.stderr,script)
                self.assertFalse(output.exists(),script)

if __name__ == '__main__': unittest.main()
