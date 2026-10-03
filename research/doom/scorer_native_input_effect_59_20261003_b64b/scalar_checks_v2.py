"""Ordinary copied-data regression, outside default test discovery."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import auditor as v1
import auditor_v2 as v2

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'formal_01/candidate/result'


def mutate(raw, name):
    row = raw['rows'][0]
    events = row['events']
    first = lambda kind: next(e for e in events if e['kind'] == kind)
    if name == 'joined_bool_sample_index':
        row['samples'][0]['index'] = False
        first('sample_begin')['index'] = False
        first('sample_end')['index'] = False
    elif name == 'joined_float_native_read_request':
        first('read')['requested'] = 65536.0
    elif name == 'joined_wrong_native_read_request':
        first('read')['requested'] = 7
    elif name == 'joined_bool_sink_count':
        first('sink_end')['count'] = True
    elif name == 'joined_float_prequeue_written':
        first('prequeued')['written'] = 10.0
    elif name == 'joined_float_read_limit':
        first('read')['limit'] = 65536.0
    elif name == 'joined_float_clock_line':
        first('clock')['line'] = float(first('clock')['line'])
    elif name == 'joined_integer_wait_ready':
        first('wait_end')['ready'] = 1
    else:
        raise ValueError(name)


CONTROL_SPECS = (
    ('joined_bool_sample_index', 'n00:V2_SAMPLE_INDEX_TYPE'),
    ('joined_float_native_read_request', 'n00:V2_READ_REQUEST_TYPE'),
    ('joined_wrong_native_read_request', 'n00:V2_READ_REQUEST_VALUE'),
    ('joined_bool_sink_count', 'n00:V2_SINK_COUNT_TYPE'),
    ('joined_float_prequeue_written', 'n00:V2_PREQUEUE_WRITTEN_TYPE'),
    ('joined_float_read_limit', 'n00:V2_READ_LIMIT_TYPE'),
    ('joined_float_clock_line', 'n00:V2_CLOCK_LINE_TYPE'),
    ('joined_integer_wait_ready', 'n00:V2_WAIT_READY_TYPE'),
)


def rejoin(row, root):
    path = root / row['case']['id'] / 'row.json'
    stripped = {k: v for k, v in row.items()
                if k not in ('artifacts', 'process_receipt')}
    data = (json.dumps(stripped, ensure_ascii=False, sort_keys=True,
                       indent=2) + '\n').encode()
    path.write_bytes(data)
    row['artifacts'][str(path.relative_to(root))] = {
        'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def exercise_controls(raw, deck, root):
    result = []
    for name, required in CONTROL_SPECS:
        changed = copy.deepcopy(raw)
        mutate(changed, name)
        with tempfile.TemporaryDirectory(prefix='native-scalar-data-') as tmp:
            copied = Path(tmp) / 'result'
            shutil.copytree(root, copied)
            rejoin(changed['rows'][0], copied)
            old_errors = v1.verify(changed, deck, copied)
            new_errors = v2.verify(changed, deck, copied)
            result.append({'name': name, 'required': required,
                           'v1_errors': old_errors, 'v2_errors': new_errors,
                           'rejoined_row_artifact':
                               changed['rows'][0]['artifacts']['n00/row.json'],
                           'rejected_for_required_reason': required in new_errors})
    return result


class ScalarChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads((ROOT / 'RAW.json').read_text())
        cls.deck = json.loads((HERE / 'deck.json').read_text())
        cls.controls = exercise_controls(cls.raw, cls.deck, ROOT)

    def test_original_sixteen_rows_remain_valid(self):
        self.assertEqual(v2.verify(self.raw, self.deck, ROOT), [])

    def test_each_rejoined_scalar_control_has_named_rejection(self):
        for c in self.controls:
            with self.subTest(name=c['name']):
                self.assertTrue(c['rejected_for_required_reason'], c)

    def test_original_checker_acceptance_is_preserved(self):
        self.assertEqual(len(self.controls), 8)
        self.assertTrue(all(c['v1_errors'] == [] for c in self.controls))

    def test_original_ten_controls_still_reject(self):
        controls = v1.controls(self.raw, self.deck, ROOT)
        self.assertEqual(len(controls), 10)
        self.assertTrue(all(c['rejected_for_required_reason'] for c in controls))


if __name__ == '__main__':
    unittest.main()
