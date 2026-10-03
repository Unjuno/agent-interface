"""Review regression: JSON boolean/integer/float types are evidence identity."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scalar_corruptions(raw):
    for name, case_id, path, value in (
        ('accepted_false_to_int', 'os-0', ('admit', 'accepted'), 0),
        ('accepted_true_to_int', 'valid-linux-screen_physical_px-supported', ('admit', 'accepted'), 1),
        ('ready_false_to_int', 'valid-linux-screen_physical_px-supported', ('readiness', 'ready'), 0),
        ('valid_true_to_int', 'valid-linux-screen_physical_px-supported', ('validate', 'valid'), 1),
        ('input_false_to_int', 'os-1', ('manifest', 'platform', 'os'), 0),
        ('input_true_to_int', 'state-2', ('manifest', 'capabilities', 'input.release_all', 'state'), 1),
        ('input_int_to_float', 'os-3', ('manifest', 'platform', 'os'), 0.0),
        ('accepted_true_to_float', 'valid-linux-screen_physical_px-supported', ('admit', 'accepted'), 1.0),
        ('ready_false_to_float', 'valid-linux-screen_physical_px-supported', ('readiness', 'ready'), 0.0),
    ):
        copy = deepcopy(raw)
        row = next(row for row in copy['rows'] if row['id'] == case_id)
        for key in path[:-1]:
            row = row[key]
        row[path[-1]] = value
        yield name, copy


class AuditScalarTypesTests(unittest.TestCase):
    def setUp(self):
        self.v1 = load('audit_matrix')
        self.v2 = load('audit_matrix_v2')
        self.fixtures = json.loads((HERE / 'fixtures.json').read_text())
        self.identity = json.loads((HERE / 'SOURCE_MANIFEST.json').read_text())
        self.raw = json.loads((HERE / 'after.json').read_text())
        self.source = self.identity['after_source_sha256']

    def test_original_audit_characterization_exposes_all_scalar_blind_spots(self):
        for name, raw in scalar_corruptions(self.raw):
            with self.subTest(name=name):
                self.assertEqual(self.v1.verify(raw, self.fixtures, False, self.source), [])

    def test_v2_rejects_each_scalar_type_corruption(self):
        for name, raw in scalar_corruptions(self.raw):
            with self.subTest(name=name):
                self.assertTrue(self.v2.verify(raw, self.fixtures, False, self.source))

    def test_v2_accepts_both_unmodified_records(self):
        for stage in ('before', 'after'):
            with self.subTest(stage=stage):
                raw = json.loads((HERE / (stage + '.json')).read_text())
                self.assertEqual(self.v2.verify(raw, self.fixtures, stage == 'before',
                                               self.identity[stage + '_source_sha256']), [])


if __name__ == '__main__':
    unittest.main()
