"""Saved-byte auditor tests; never imports the historical harness/owners."""
import hashlib
import json
from pathlib import Path
import unittest

from audit_saved_v2 import AuditError, audit_saved

ROOT = Path(__file__).resolve().parent


class SavedAuditTests(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_bytes()

    def test_retained_packet(self):
        result = audit_saved(self.read)
        self.assertEqual(result['pairs'], 10)
        self.assertEqual(result['runs'], 20)
        self.assertEqual(result['logs_matched'], 20)
        self.assertAlmostEqual(result['paired_reduction_median_ms'], 148.408, places=3)

    def test_coherent_result_corruptions_are_rejected(self):
        for mutation in (
                lambda row: row['executor'].update(terminal_status='completed'),
                lambda row: row['executor'].update(held_key_to_verified_release_ms=float('nan')),
                lambda row: row['executor'].update(pending_answer_eligible=True),
                lambda row: row['admission'].update(grants_input_authority=True),
                lambda row: row['timestamps_ns'].update(executor_cancel=row['timestamps_ns']['planner_interrupt']),
                lambda row: row['executor']['release'].update(keys_down=[65]),
                lambda row: row['executor'].update(injected_delay_ms=150.031473)):
            with self.subTest(mutation=mutation):
                row = json.loads(self.read('results/pair-01-early.json'))
                mutation(row)
                raw = json.dumps(row).encode()
                log_path = 'results/logs/pair-01-early.log'
                log = b'wsl: kernel does not support swap limit\n' + raw
                manifest = json.loads(self.read('CUSTODY_20261016.json'))
                item = next(v for v in manifest['files'] if v['path'] == log_path)
                item.update(bytes=len(log), sha256=hashlib.sha256(log).hexdigest())
                replacements = {'results/pair-01-early.json': raw, log_path: log,
                                'CUSTODY_20261016.json': json.dumps(manifest).encode()}
                with self.assertRaises(AuditError):
                    audit_saved(lambda rel: replacements[rel] if rel in replacements else self.read(rel))

    def test_order_hash_and_missing_log_are_rejected(self):
        rows = json.loads(self.read('results/run-status.json'))
        rows[1] = rows[0]
        cases = [
            {'results/run-status.json': json.dumps(rows).encode()},
            {'worktree/research/live_control/observable_signal_guard_v2.py': b'changed'},
            {'results/logs/pair-01-early.log': b'changed'},
        ]
        for replacements in cases:
            with self.subTest(paths=list(replacements)), self.assertRaises(AuditError):
                audit_saved(lambda rel: replacements[rel] if rel in replacements else self.read(rel))
        def missing(rel):
            if rel == 'results/logs/pair-01-early.log':
                raise FileNotFoundError(rel)
            return self.read(rel)
        with self.assertRaises((AuditError, FileNotFoundError)):
            audit_saved(missing)


if __name__ == '__main__':
    unittest.main()
