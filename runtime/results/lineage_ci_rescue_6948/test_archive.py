import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
SOURCE = 'c32d4d6f683586e87047ae24f3b6664cb6d95d09'
PACKET = 'research/integration/lineage_ci_2428_20261003_01a0ff58'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


class Custody(unittest.TestCase):
    def test_original_packet_and_historical_sources(self):
        files = git('ls-tree', '-r', '--name-only', SOURCE, '--', PACKET).decode().splitlines()
        self.assertEqual(len(files), 26)
        for path in files:
            self.assertEqual((ROOT / path).read_bytes(), git('show', f'{SOURCE}:{path}'))
        manifest = json.loads((ROOT / PACKET / 'MANIFEST.json').read_bytes())
        self.assertEqual(len(manifest['entries']), 25)
        for entry in manifest['entries']:
            data = (ROOT / PACKET / entry['path']).read_bytes()
            self.assertEqual(len(data), entry['bytes'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), entry['sha256'])
        for entry in json.loads((ROOT / PACKET / 'HISTORICAL_CUSTODY.json').read_bytes()):
            data = git('show', f"{entry['source_commit']}:{entry['source_path']}")
            self.assertEqual(data, (ROOT / PACKET / entry['copy_path']).read_bytes())
            self.assertEqual(len(data), entry['bytes'])

    def test_corrected_workflow_custody_and_replacement_routing(self):
        saved = Path(__file__).with_name('PRIOR_WORKFLOW.actual.yml.txt').read_bytes()
        self.assertEqual(saved, git('show', f'{SOURCE}^:.github/workflows/cli-v1-lineage-freshness-2428.yml'))
        self.assertEqual(len(saved), 682)
        self.assertEqual((ROOT / PACKET / 'PRIOR_WORKFLOW.yml.txt').read_bytes(), saved)
        workflow = (ROOT / '.github/workflows/runtime-cli-v1.yml').read_text()
        for module in ['runtime.cli_v1.test_lineage_freshness', 'runtime.cli_v1.test_lineage_json_identity']:
            self.assertIn(module, workflow)
        self.assertIn('unittest discover -s runtime/motor_state_v1', workflow)


if __name__ == '__main__':
    unittest.main()
