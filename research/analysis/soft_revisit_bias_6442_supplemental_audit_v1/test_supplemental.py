"""Regression controls over immutable A03 raw; no candidate execution."""
import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


def module_at(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RetainedRawRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = [json.loads(line) for line in Path(os.environ['RETAINED_RAW']).read_bytes().splitlines()]
        if os.environ.get('LEGACY_AUDIT_SOURCE'):
            source = Path(os.environ['LEGACY_AUDIT_SOURCE'])
            fixtures = module_at('regression_fixtures', source / 'fixtures.py').build_fixtures()
            audit = module_at('regression_legacy_audit', source / 'audit.py').audit_rows
            cls.evaluate = staticmethod(lambda rows: audit(fixtures, rows))
            cls.pass_decision = 'PASS_METHOD_SCOPED'
        else:
            from audit_v1 import audit_rows
            cls.evaluate = staticmethod(audit_rows)
            cls.pass_decision = 'PASS_RETAINED_TRANSCRIPT_SCOPED'

    def reject(self, rows):
        result = self.evaluate(rows)
        self.assertNotEqual(result['decision'], self.pass_decision)
        self.assertTrue(result['errors'])

    def test_original_raw_and_all_baseline_counts_remain_valid(self):
        result = self.evaluate(copy.deepcopy(self.rows))
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['decision'], self.pass_decision)
        self.assertEqual(result['rows'], 128)
        self.assertEqual(result['successes'], {
            'stateless': {'stable': 8, 'partial_revision': 16},
            'hard': {'stable': 8, 'partial_revision': 0},
            'soft': {'stable': 8, 'partial_revision': 16},
            'exhaustive': {'stable': 8, 'partial_revision': 0},
        })

    def test_declared_zero_budget_cannot_certify_three_events(self):
        rows = copy.deepcopy(self.rows)
        rows[0]['budget'] = 0
        self.reject(rows)

    def test_stateless_cannot_refuse_before_observing_eligible_safe_edge(self):
        rows = copy.deepcopy(self.rows)
        row = next(r for r in rows if r['fixture_id'] == 'no_target-00' and r['policy'] == 'stateless')
        row.update(events=[{'type': 'refuse', 'reason': 'fabricated'}], event_count=1, observed_labels=[], claimed_target=None)
        self.reject(rows)

    def test_boolean_source_epoch_cannot_impersonate_integer_identity(self):
        rows = copy.deepcopy(self.rows)
        rows[0]['events'][0]['source_epoch'] = True
        self.reject(rows)

    def test_float_budget_cannot_impersonate_integer_budget(self):
        rows = copy.deepcopy(self.rows)
        rows[0]['budget'] = 12.0
        self.reject(rows)

    def test_duplicate_pair_cannot_replace_missing_pair(self):
        rows = copy.deepcopy(self.rows)
        rows[-1] = copy.deepcopy(rows[0])
        self.reject(rows)

    def test_target_cannot_be_followed_by_tail_input(self):
        rows = copy.deepcopy(self.rows)
        rows[0]['events'].append({'type': 'navigate', 'edge_id': 'alpha'})
        rows[0]['event_count'] += 1
        self.reject(rows)

    def test_unknown_row_field_is_not_silently_discarded(self):
        rows = copy.deepcopy(self.rows)
        rows[0]['unknown'] = 'altered'
        self.reject(rows)

    def test_missing_pair_cannot_pass_coverage(self):
        self.reject(copy.deepcopy(self.rows[:-1]))


@unittest.skipIf(os.environ.get('LEGACY_AUDIT_SOURCE'), 'CLI controls belong to supplemental version')
class SupplementalCliTests(unittest.TestCase):
    def invoke(self, raw, preexisting_output=None):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / 'raw.jsonl', Path(directory) / 'audit.json'
            source.write_bytes(raw)
            if preexisting_output is not None:
                output.write_bytes(preexisting_output)
            result = subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('audit_v1.py')),
                                     '--input', str(source), '--output', str(output)],
                                    capture_output=True, check=False)
            self.assertEqual(source.read_bytes(), raw)
            return result.returncode, output.read_bytes() if output.exists() else None

    def test_original_raw_cli_preserves_counts_and_input(self):
        code, output = self.invoke(Path(os.environ['RETAINED_RAW']).read_bytes())
        self.assertEqual(code, 0)
        result = json.loads(output)
        self.assertEqual(result['rows'], 128)
        self.assertEqual(result['decision'], 'PASS_RETAINED_TRANSCRIPT_SCOPED')

    def test_duplicate_budget_key_does_not_disappear_during_json_parse(self):
        raw = Path(os.environ['RETAINED_RAW']).read_bytes()
        code, output = self.invoke(raw.replace(b'{', b'{"budget":0,', 1))
        self.assertEqual(code, 1)
        self.assertTrue(json.loads(output)['errors'])

    def test_oversized_input_does_not_receive_a_full_input_hash(self):
        code, output = self.invoke(b' ' * (1024 * 1024 + 2))
        self.assertEqual(code, 1)
        result = json.loads(output)
        self.assertIsNone(result['input_sha256'])
        self.assertTrue(result['input_prefix_sha256'])

    def test_existing_output_is_preserved(self):
        sentinel = b'keep original audit bytes\n'
        code, output = self.invoke(b'{}\n', preexisting_output=sentinel)
        self.assertEqual(code, 2)
        self.assertEqual(output, sentinel)


if __name__ == '__main__':
    unittest.main()
