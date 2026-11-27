"""Corruption controls for the saved reader; no historical runner imports."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from audit_saved import EvidenceError, load_evidence, validate_records


class SavedRegressionAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = load_evidence(Path(__file__).resolve().parents[3])

    def check_bad(self, change):
        evidence = copy.deepcopy(self.evidence)
        change(evidence)
        self.assertNotEqual(evidence['files'], self.evidence['files'], 'mutation must alter retained bytes')
        # Coherently rehash copies so rejection cannot rely on stale checksums.
        for attempt in ('a11', 'a12'):
            key = f'{attempt}/SHA256SUMS.txt'
            evidence['files'][key] = ''.join(
                f"{hashlib.sha256(evidence['files'][f'{attempt}/{name}']).hexdigest()}  {name}\n"
                for line in evidence['files'][key].decode().splitlines()
                for _, name in [line.split('  ', 1)]).encode()
        with self.assertRaises(EvidenceError):
            validate_records(evidence)

    def edit_json(self, evidence, attempt, name, change):
        key = f'{attempt}/{name}.json'
        row = json.loads(evidence['files'][key])
        change(row)
        evidence['files'][key] = json.dumps(row).encode()

    def test_retains_first_failure_and_corrected_saved_success(self):
        result = validate_records(self.evidence)
        self.assertEqual(result['decisions'], {'a11': 'FAIL', 'a12': 'PASS'})
        self.assertEqual(result['saved_test_executions'], 216)
        self.assertEqual(result['source_count'], 34)

    def test_first_failure_cannot_be_promoted(self):
        self.check_bad(lambda e: self.edit_json(e, 'a11', 'RESULT', lambda r: r.update(decision='PASS')))

    def test_boolean_exit_is_not_a_zero_receipt(self):
        self.check_bad(lambda e: self.edit_json(e, 'a12', 'RESULT', lambda r: r['runs']['controller']['normal'].update(exit_code=False)))

    def test_count_change_rejected(self):
        self.check_bad(lambda e: self.edit_json(e, 'a12', 'FREEZE', lambda r: r['suites'][0].update(tests=15)))

    def test_missing_or_duplicate_test_identity_rejected(self):
        def change(e):
            key = 'a12/controller.normal.stderr.txt'
            lines = e['files'][key].splitlines(keepends=True)
            lines[1] = lines[0]
            e['files'][key] = b''.join(lines)
        self.check_bad(change)

    def test_mode_identity_disagreement_rejected(self):
        def change(e):
            key = 'a12/controller.optimized.stderr.txt'
            e['files'][key] = e['files'][key].replace(b'test_authored_cover_still_uses_original_guard', b'test_unrelated_control', 1)
        self.check_bad(change)

    def test_source_digest_rejected(self):
        def change(r):
            next(iter(r['sources'].values()))['sha256'] = '0' * 64
        self.check_bad(lambda e: self.edit_json(e, 'a12', 'RESULT', change))

    def test_missing_carry_source_rejected(self):
        self.check_bad(lambda e: self.edit_json(e, 'a12', 'MAIN_CARRY_FORWARD', lambda r: r['sources'].pop()))

    def test_forged_carry_diff_count_rejected(self):
        self.check_bad(lambda e: self.edit_json(e, 'a12', 'MAIN_CARRY_FORWARD', lambda r: r.update(changed_paths_since_frozen_source=0)))

    def test_wrong_suite_module_in_both_modes_rejected(self):
        def change(e):
            for mode in ('normal', 'optimized'):
                key = f'a12/controller.{mode}.stderr.txt'
                e['files'][key] = e['files'][key].replace(b'(test_map01_overlap_controller_v39.', b'(test_unrelated_module.')
        self.check_bad(change)

    def test_failed_log_cannot_keep_successful_summary(self):
        def change(e):
            key = 'a12/controller.normal.stderr.txt'
            e['files'][key] = e['files'][key].replace(b'OK', b'FAILED (failures=1)')
        self.check_bad(change)


if __name__ == '__main__':
    unittest.main()
