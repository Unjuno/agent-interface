"""Excluded construction checks; no retained matrix is invoked."""
import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest

import audit
from candidate.reader import read_pending, _finite_float

ROOT = Path(__file__).resolve().parent

class Construction(unittest.TestCase):
    def test_exact_sources(self):
        for name, wanted in [('upstream/reader.py', 'ea72c166c2cea511ea91031dfbb14563fe4e3245'),
                             ('upstream/__main__.py', '1a97a659113666ccaa254ab2bf5dc0306e217015')]:
            data = (ROOT / name).read_bytes()
            self.assertEqual(hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(), wanted)
        self.assertEqual((ROOT/'candidate/__main__.py').read_bytes(), (ROOT/'upstream/__main__.py').read_bytes())
    def test_finite_values(self):
        for token in ['1.25', '1.7976931348623157e308', '5e-324', '1e-400']:
            self.assertTrue(math.isfinite(_finite_float(token)))
    def test_overflow(self):
        for token in ['1e309', '-1e309', '1.7976931348623159e308']:
            with self.assertRaises(ValueError):
                _finite_float(token)
    def test_signed_zero(self):
        self.assertEqual(math.copysign(1, _finite_float('-0.0')), -1)
    def test_prefix_and_cursor(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name)/'stream'
            prefix = b'{"event":"ok","delivery_id":"delivery:1"}\n'
            path.write_bytes(prefix+b'{"event":"next","delivery_id":"delivery:2","v":[1e400]}\n')
            result = read_pending(path, stream_id='test')
            self.assertEqual(result['problem'], 'INVALID_JSON_RECORD')
            self.assertEqual(result['next_cursor']['offset'], len(prefix))
            again = read_pending(path, stream_id='test', cursor=result['next_cursor'])
            self.assertEqual(again['records'], [])
            self.assertEqual(again['next_cursor'], result['next_cursor'])
    def test_incomplete_before_parse(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name)/'stream'
            path.write_text('{"event":"ok","delivery_id":"delivery:1","v":1e400}')
            result = read_pending(path, stream_id='test')
            self.assertEqual(result['tail_state'], 'incomplete')
            self.assertEqual(result['next_cursor']['offset'], 0)
    def test_oracle_independent_decimal(self):
        cases = json.loads((ROOT/'CASES.json').read_text())
        self.assertEqual(sum(audit.expected(c, 'upstream', 'full') is None for c in cases), 5)
        self.assertTrue(all(audit.expected(c, 'candidate', 'full') is not None for c in cases))
        self.assertTrue(all(audit.expected(c, 'upstream', 'first')['tail_state']=='limit' for c in cases))
    def test_exact_candidate_delta(self):
        source = (ROOT/'upstream/reader.py').read_text()
        source = source.replace('import json\n','import json\nimport math\n',1)
        source = source.replace('def _integer(value, minimum, maximum):',
            "def _finite_float(value):\n    number = float(value)\n    if not math.isfinite(number):\n        raise ValueError('JSON float outside finite range')\n    return number\n\n\ndef _integer(value, minimum, maximum):",1)
        source = source.replace('object_pairs_hook=_unique_object, parse_constant=_invalid_constant)',
            'object_pairs_hook=_unique_object, parse_constant=_invalid_constant,\n                                parse_float=_finite_float)',1)
        self.assertEqual(source, (ROOT/'candidate/reader.py').read_text())

if __name__ == '__main__':
    unittest.main()
