from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest


PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]
AUDITOR = PACKAGE / 'audit_v2.py'
CANDIDATE = PACKAGE / 'results' / 'candidate.json'


class FinalAdmissionAuditTests(unittest.TestCase):
    def run_auditor(self, mutate=None):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = root / 'research' / 'doom' / PACKAGE.name
            results = package / 'results'
            results.mkdir(parents=True)
            shutil.copyfile(AUDITOR, package / 'audit_v2.py')
            candidate = json.loads(CANDIDATE.read_text(encoding='utf-8'))
            if mutate is not None:
                mutate(candidate)
            (results / 'candidate.json').write_text(
                json.dumps(candidate, indent=2, sort_keys=True) + '\n', encoding='utf-8')
            for relative in (
                Path('research/doom/map01_overlap_controller_v39.py'),
                Path('research/live_control/observable_signal_guard_v2.py'),
            ):
                source = ROOT / relative
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
            return subprocess.run(
                [sys.executable, str(package / 'audit_v2.py')],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )

    def test_frozen_candidate_still_passes(self):
        result = self.run_auditor()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'PASS_SCOPED_REPLAY')
        self.assertEqual(json.loads(result.stdout)['independent_assertions'], 11)

    def test_rejects_noninvalidated_final_admission(self):
        result = self.run_auditor(lambda raw: raw['final_admission'].__setitem__(
            'status', 'READY_FOR_ACTION_VALIDITY'))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'FAIL')

    def test_rejects_admitted_input_authority_after_invalidation(self):
        result = self.run_auditor(lambda raw: raw['final_admission'].__setitem__(
            'input_authority_admitted', True))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'FAIL')


if __name__ == '__main__':
    unittest.main(verbosity=2)
