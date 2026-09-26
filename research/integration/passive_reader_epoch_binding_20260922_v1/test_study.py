"""Construction-only wrapper checks and raw-evidence corruption challenges."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from audit import audit_document
from candidate import read_epoch_bound

ROOT = Path(__file__).resolve().parent


def corruptions(raw):
    cases = {}
    value = copy.deepcopy(raw)
    value['cases'].pop()
    cases['missing_case'] = value
    value = copy.deepcopy(raw)
    value['cases'][-1] = copy.deepcopy(value['cases'][0])
    cases['duplicate_case'] = value
    value = copy.deepcopy(raw)
    value['cases'][0]['producers'][0]['config']['epoch'] = 'other'
    cases['wrong_epoch'] = value
    value = copy.deepcopy(raw)
    snapshot = value['cases'][0]['snapshots']['final']
    snapshot['utf8'] = snapshot['utf8'].replace('"value":3', '"value":9')
    snapshot['sha256'] = hashlib.sha256(snapshot['utf8'].encode()).hexdigest()
    cases['payload_changed_with_rehashed_snapshot'] = value
    value = copy.deepcopy(raw)
    receipt = json.loads(value['cases'][0]['reads'][1]['stdout_utf8'])
    receipt['result']['receipt']['input_dispatched'] = True
    value['cases'][0]['reads'][1]['stdout_utf8'] = json.dumps(receipt) + '\n'
    cases['authority_changed'] = value
    value = copy.deepcopy(raw)
    del value['cases'][0]['producers'][0]['returncode']
    cases['missing_exit'] = value
    value = copy.deepcopy(raw)
    value['cases'][0]['producers'][0]['returncode'] = False
    cases['boolean_exit_code'] = value
    value = copy.deepcopy(raw)
    request = json.loads(value['cases'][0]['reads'][1]['request_utf8'])
    request['cursor']['prefix_sha256'] = '0' * 64
    value['cases'][0]['reads'][1]['request_utf8'] = json.dumps(request) + '\n'
    cases['changed_cursor_hash'] = value
    return cases


def rejected_by_auditor(value):
    try:
        return audit_document(value)['audit'] != 'PASS'
    except (ValueError, KeyError, TypeError, IndexError):
        return True


class EpochGateTests(unittest.TestCase):
    def invoke(self, records, epoch='A'):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'records.jsonl'
            data = ''.join(json.dumps(x) + '\n' for x in records).encode()
            path.write_bytes(data)
            try:
                return read_epoch_bound(path, stream_id=epoch)
            finally:
                self.assertEqual(path.read_bytes(), data)

    def test_matching_epoch(self):
        result = self.invoke([{'event': 'ready', 'delivery_id': 'delivery:1', 'producer_epoch': 'A'}])
        self.assertEqual(len(result['records']), 1)
        self.assertIs(result['input_dispatched'], False)

    def test_missing_epoch(self):
        with self.assertRaisesRegex(ValueError, 'PRODUCER_EPOCH_MISMATCH'):
            self.invoke([{'event': 'ready', 'delivery_id': 'delivery:1'}])

    def test_wrong_epoch(self):
        with self.assertRaisesRegex(ValueError, 'PRODUCER_EPOCH_MISMATCH'):
            self.invoke([{'event': 'ready', 'delivery_id': 'delivery:1', 'producer_epoch': 'B'}])

    def test_wrong_epoch_type(self):
        with self.assertRaisesRegex(ValueError, 'PRODUCER_EPOCH_MISMATCH'):
            self.invoke([{'event': 'ready', 'delivery_id': 'delivery:1', 'producer_epoch': True}])

    def test_mixed_batch_not_partially_returned(self):
        with self.assertRaisesRegex(ValueError, 'PRODUCER_EPOCH_MISMATCH'):
            self.invoke([{'event': 'ready', 'delivery_id': 'delivery:1', 'producer_epoch': 'A'},
                         {'event': 'ready', 'delivery_id': 'delivery:2', 'producer_epoch': 'B'}])

    def test_empty_is_not_completion_or_ack(self):
        result = self.invoke([])
        self.assertEqual(result['records'], [])
        self.assertEqual(result['authority'], 'none')
        self.assertIs(result['acknowledged'], False)
        self.assertNotIn('producer_terminated', result)


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = Path(os.environ.get('EPOCH_CONSTRUCTION_RAW', ROOT / 'construction-02/RAW.json'))
        cls.before = cls.path.read_bytes()
        cls.raw = json.loads(cls.before)

    def test_original(self):
        result = audit_document(self.raw)
        self.assertEqual(result['errors'], [])

    def test_eight_mutations(self):
        controls = {}
        for name, value in corruptions(self.raw).items():
            with self.subTest(mutation=name):
                controls[name] = rejected_by_auditor(value)
                self.assertTrue(controls[name], name)
        self.assertEqual(self.path.read_bytes(), self.before)
        if os.environ.get('EPOCH_CONTROL_OUTPUT'):
            with Path(os.environ['EPOCH_CONTROL_OUTPUT']).open('x') as file:
                json.dump(controls, file, sort_keys=True, indent=2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
