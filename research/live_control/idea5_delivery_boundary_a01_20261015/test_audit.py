import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from audit import audit

ROOT = Path(__file__).resolve().parent


class AuditMutationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.output = Path(temp.name) / 'copy'
        shutil.copytree(ROOT / 'output-normal', self.output)

    def rewrite(self, case, filename, change):
        path = self.output / case / filename
        records = [json.loads(line) for line in path.read_text().splitlines()]
        path.write_text(''.join(json.dumps(r) + '\n' for r in change(copy.deepcopy(records))))

    def test_retained_eight_case_matrix_is_accepted(self):
        self.assertEqual(audit(self.output)['status'], 'PASS_SCOPED_RAW_AUDIT')

    def test_missing_explicit_critical_event_is_rejected(self):
        self.rewrite('v15-compact-healthy', 'delivered.jsonl',
                     lambda rr: [r for r in rr if r['event'] != 'critical_signal'])
        with self.assertRaises(ValueError):
            audit(self.output)

    def test_false_successful_flush_on_broken_stream_is_rejected(self):
        shutil.copyfile(self.output / 'v15-compact-healthy' / 'delivery-flush.jsonl',
                        self.output / 'v15-compact-broken' / 'delivery-flush.jsonl')
        with self.assertRaises(ValueError):
            audit(self.output)

    def test_broken_stream_claiming_received_rows_is_rejected(self):
        shutil.copyfile(self.output / 'v10-full-broken' / 'delivered.jsonl',
                        self.output / 'v10-full-broken' / 'captured-stdout.jsonl')
        with self.assertRaises(ValueError):
            audit(self.output)

    def test_missing_case_is_rejected(self):
        path = self.output / 'SUMMARY.json'
        value = json.loads(path.read_text())
        value['cases'].pop()
        path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            audit(self.output)


if __name__ == '__main__':
    unittest.main()
