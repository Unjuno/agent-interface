"""Eight corruption challenges against excluded construction evidence only."""
import copy
import json
from pathlib import Path
import sys
import unittest
from audit import examine

DATA = json.loads(Path(sys.argv.pop(1)).read_text()) if len(sys.argv) > 1 else None
SOURCES = copy.deepcopy(DATA['source_sha256']) if DATA else None


def mutate_response(row, fn):
    value = json.loads(row['response_raw'])
    fn(value)
    row['response_raw'] = json.dumps(value) + '\n'


class Corruptions(unittest.TestCase):
    def rejected(self, mutation):
        changed = copy.deepcopy(DATA)
        mutation(changed)
        self.assertTrue(examine(changed, SOURCES, formal=False)['errors'])

    def test_baseline(self):
        self.assertEqual(examine(DATA, SOURCES, formal=False)['errors'], [])

    def test_missing_row(self):
        self.rejected(lambda x: x['rows'].pop())

    def test_wrong_source(self):
        self.rejected(lambda x: x['source_sha256'].__setitem__('upstream/reader.py', '0'*64))

    def test_changed_payload(self):
        self.rejected(lambda x: mutate_response(x['rows'][0], lambda z: z['receipt']['records'][0].__setitem__('value', 999)))

    def test_authority(self):
        self.rejected(lambda x: mutate_response(x['rows'][0], lambda z: z['receipt'].__setitem__('acknowledged', True)))

    def test_wrong_cursor(self):
        self.rejected(lambda x: mutate_response(x['rows'][0], lambda z: z['receipt']['next_cursor'].__setitem__('offset', 0)))

    def test_unreaped(self):
        self.rejected(lambda x: x['rows'][0].__setitem__('reaped', False))

    def test_early_timeout(self):
        def change(x):
            row = next(r for r in x['rows'] if r['outcome'] == 'TIMEOUT')
            row['observed_ns'] = row['go_ns'] + 10
        self.rejected(change)

    def test_unconnected_writer(self):
        def change(x):
            row = next(r for r in x['rows'] if r['writer'])
            row['writer']['alive_during_read'] = False
        self.rejected(change)


if __name__ == '__main__':
    unittest.main(verbosity=2)
