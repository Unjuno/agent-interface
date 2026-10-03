"""Audit identity must keep a returned transition count's JSON type."""
import copy
import json
from pathlib import Path
import unittest
import audit


class AuditIdentityTests(unittest.TestCase):
    def test_boolean_or_float_transition_count_is_not_the_retained_integer(self):
        record = json.loads(Path(__file__).with_name('after.json').read_bytes())
        for replacement in (True, 1.0):
            with self.subTest(replacement=replacement):
                malformed = copy.deepcopy(record)
                row = next(r for r in malformed['rows'] if r['result'] is not None
                           and r['result']['completed_transitions'] == 1)
                row['result']['completed_transitions'] = replacement
                self.assertTrue(audit.audit(malformed)['errors'])


if __name__ == '__main__':
    unittest.main()
