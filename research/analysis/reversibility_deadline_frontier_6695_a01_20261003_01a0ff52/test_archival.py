"""Read-only receipt checks; never launch a formal producer or wrapper."""
import hashlib
import json
from pathlib import Path
import unittest

import auditor

ROOT = Path(__file__).resolve().parent


class ArchivalChecks(unittest.TestCase):
    def test_original_manifest_and_frozen_sources(self):
        lines = (ROOT / 'SHA256SUMS').read_text().splitlines()
        self.assertEqual(len(lines), 20)
        for line in lines:
            expected, name = line.split(None, 1)
            self.assertEqual(hashlib.sha256((ROOT / name.strip()).read_bytes()).hexdigest(), expected)
        freeze = json.loads((ROOT / 'FREEZE.json').read_text())
        self.assertEqual(len(freeze['source_sha256']), 7)
        for name, expected in freeze['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected)

    def test_saved_raw_audit_exact_and_conditional_frontier(self):
        raw = (ROOT / 'formal_01/candidate/RAW.jsonl').read_bytes()
        result = auditor.audit(json.loads((ROOT / 'fixtures.json').read_text()),
                               json.loads((ROOT / 'truth.json').read_text()),
                               [json.loads(line) for line in raw.splitlines()])
        result['raw_sha256'] = hashlib.sha256(raw).hexdigest()
        self.assertEqual(result, json.loads((ROOT / 'formal_01/audit/AUDIT.json').read_text()))
        self.assertEqual(result['rows'], 6912)
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['diagnostics'], {
            'stage_only_correct_on_time': 10, 'wait_only_correct_on_time': 22,
            'stage_equality_admits': 36, 'stage_one_ms_short_refuses': 36})
        self.assertGreater(result['counts']['WAIT_THEN_PREPARE']['correct_commit'],
                           result['counts']['STAGE_THEN_CORRECT']['correct_commit'])

    def test_original_execution_receipt_scope(self):
        receipt = json.loads((ROOT / 'EXECUTION.json').read_text())
        self.assertEqual((receipt['candidate_invocations'], receipt['auditor_invocations'],
                          receipt['retries']), (1, 1, 0))
        self.assertEqual(receipt['freeze_sha256'], hashlib.sha256((ROOT / 'FREEZE.json').read_bytes()).hexdigest())
        self.assertEqual([r['stage'] for r in receipt['records']], ['candidate', 'audit'])
        for record in receipt['records']:
            self.assertEqual(record['exit_code'], 0)
        candidate_argv = receipt['records'][0]['argv']
        self.assertFalse(any('truth.json' in arg for arg in candidate_argv))
        self.assertFalse(json.loads((ROOT / 'FREEZE.json').read_text())['machine_isolated_mode'])


if __name__ == '__main__':
    unittest.main()
