"""Exercise CI sparse selection against the archival jobs' real dependencies."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class SparseCheckoutDependencies(unittest.TestCase):
    def test_ci_selects_archival_tests_and_their_original_data(self):
        # Use the index: CI restores a historical workflow into the worktree
        # for unrelated provenance tests, without changing the staged CI config.
        workflow = subprocess.check_output(
            ['git', 'show', ':.github/workflows/analysis-index.yml'], cwd=ROOT, text=True)
        lines = workflow.splitlines()
        start = next(i for i, line in enumerate(lines) if line.strip() == 'sparse-checkout: |')
        field_indent = len(lines[start]) - len(lines[start].lstrip())
        paths = []
        for line in lines[start + 1:]:
            if line.strip() and len(line) - len(line.lstrip()) <= field_indent:
                break
            if line.strip():
                paths.append(line.strip())
        required = {
            'research/analysis/check_index.py',
            'research/integration/core_admission_composition_57_20261003_01a0ff59/test_archival.py',
            'research/integration/pr6863_review_rescue_20261003/test_archival.py',
            'research/integration/pr6863_review_20261003_01a0ff58/verify.py',
            'research/integration/teardown_witness_review_rescue_20261003/test_archival.py',
            'research/integration/owner_keyup_teardown_witness_5156_01a0ff58/witness_audit.py',
        }
        with tempfile.TemporaryDirectory(prefix='analysis-checkout-rules-') as tmp:
            rules = Path(tmp) / 'rules'
            rules.write_text('\n'.join(paths) + '\n')
            selected = subprocess.check_output(
                ['git', 'sparse-checkout', 'check-rules', '--cone', '--rules-file', str(rules)],
                cwd=ROOT, input='\n'.join(sorted(required)) + '\n', text=True)
        self.assertEqual(set(selected.splitlines()), required,
                         'CI excludes archival test/data inputs: ' + ', '.join(sorted(required - set(selected.splitlines()))))


if __name__ == '__main__':
    unittest.main()
