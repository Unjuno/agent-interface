"""Directed corruption checks against retained actual decoder raw."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from audit import inspect

ROOT = Path(__file__).parent


class MarkerAuditControls(unittest.TestCase):
    def test_eight_corruptions_are_rejected(self):
        raw = json.loads((ROOT / 'raw.json').read_bytes())
        cases = json.loads((ROOT / 'fixtures.json').read_bytes())
        frozen_bytes = (ROOT / 'FREEZE.json').read_bytes()
        frozen = json.loads(frozen_bytes)
        inspect(raw, cases, frozen, frozen_bytes)
        for name in ('drop', 'duplicate', 'source', 'input_hash', 'input_mutation',
                     'false_accept', 'false_refusal', 'result_scalar_type'):
            with self.subTest(name=name):
                value = deepcopy(raw)
                if name == 'drop': value['rows'].pop()
                elif name == 'duplicate': value['rows'].append(deepcopy(value['rows'][0]))
                elif name == 'source': value['source_sha256']['fixed'] = '0' * 64
                elif name == 'input_hash': value['rows'][0]['input_sha256'] = '0' * 64
                elif name == 'input_mutation': value['rows'][0]['input_unchanged'] = False
                elif name == 'false_accept':
                    row = next(r for r in value['rows'] if r['arm'] == 'fixed' and r['id'] == 'decode.0.0.0')
                    row['observed'] = {'status': 'returned', 'result': {}}
                elif name == 'false_refusal':
                    row = next(r for r in value['rows'] if r['arm'] == 'fixed' and r['id'] == 'decode.0.0.2')
                    row['observed'] = {'status': 'error', 'exception': 'ValueError', 'message': 'event reference marker mismatch'}
                else:
                    row = next(r for r in value['rows'] if r['arm'] == 'fixed' and r['id'] == 'literal.2')
                    row['observed']['result']['report']['value']['event_ref'] = False
                with self.assertRaises(ValueError):
                    inspect(value, cases, frozen, frozen_bytes)


if __name__ == '__main__':
    unittest.main()
