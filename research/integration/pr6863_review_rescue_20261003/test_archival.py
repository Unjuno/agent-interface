"""Saved-data review checks; no original probe or runtime execution."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ARCHIVE = Path(__file__).resolve().parent.parent / 'pr6863_review_20261003_01a0ff58'


class ArchivalChecks(unittest.TestCase):
    def test_original_manifest_verifier_and_author_counterexamples(self):
        result = subprocess.run([sys.executable, '-B', str(ARCHIVE / 'verify.py')],
                                capture_output=True, text=True, check=True)
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed['errors'], [])
        self.assertEqual(parsed['manifest_files'], 47)
        self.assertEqual(parsed['author_type_counterexamples'], 3)

    def test_v2_saved_audits_and_all_five_type_controls(self):
        spec = importlib.util.spec_from_file_location('archived_review_oracle', ARCHIVE / 'oracle_v2.py')
        oracle = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(oracle)
        for arm, malformed in [('base', 26), ('head', 0)]:
            raw = json.loads((ARCHIVE / (arm + '.json')).read_text())
            result = oracle.audit(raw)
            self.assertEqual(result['malformed_execute_entries'], malformed)
            controls = {}
            for name in ('missing_row', 'duplicate_row', 'boolean_count', 'float_identity', 'wrong_dispatch_type'):
                changed = deepcopy(raw)
                if name == 'missing_row':
                    changed['rows'].pop()
                elif name == 'duplicate_row':
                    changed['rows'][-1] = changed['rows'][0]
                elif name == 'boolean_count':
                    changed['rows'][0]['counts']['execute'] = True
                elif name == 'float_identity':
                    changed['rows'][0]['sequence'] = 0.0
                else:
                    row = next(r for r in changed['rows'] if r['kind'] == 'exact' and r['profile'] == 'valid')
                    row['dispatched'][0]['type'] = 'bool'
                controls[name] = bool(oracle.audit(changed)['errors'])
            self.assertTrue(all(controls.values()))
            result['corruption_controls_rejected'] = controls
            self.assertEqual(result, json.loads((ARCHIVE / (arm + '-audit-v2.json')).read_text()))

    def test_unresolved_original_proposal_diff_identity_is_preserved(self):
        identity = json.loads((ARCHIVE / 'proposal-identity.json').read_text())
        self.assertEqual(identity['proposal_digest'], identity['expected_proposal_digest'])
        for field in ('worktree_diff_sha256', 'head_attributes_diff_sha256'):
            self.assertNotEqual(identity[field], identity['expected_diff_sha256'])


if __name__ == '__main__':
    unittest.main()
