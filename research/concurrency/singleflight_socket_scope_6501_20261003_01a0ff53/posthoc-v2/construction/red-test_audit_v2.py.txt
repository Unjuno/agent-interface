"""Retained-only regression controls; no construction/candidate imports."""
import json
import unittest
from pathlib import Path

import audit_v2
from controls import mutations

ROOT = Path(__file__).resolve().parents[1]


class WireBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads((ROOT / 'run-a01/raw.json').read_text())
        cls.fixtures = json.loads((ROOT / 'fixtures.json').read_text())

    def test_unchanged_retained_counts(self):
        result = audit_v2.audit(self.raw, self.fixtures)
        self.assertEqual(result['actual_socket_invocations'], {'independent':14, 'predicate_inflight':7, 'scope_inflight':11, 'scope_cache':10})
        self.assertEqual((result['trials'], result['callers']), (24, 56))

    def test_original_numeric_alias_acceptances_are_preserved(self):
        for name, _, changed, additional in mutations(self.raw):
            if additional:
                with self.subTest(control=name):
                    self.assertEqual(audit_v2.original.audit(changed, self.fixtures)['status'], 'PASS_SOCKET_SCOPE_TRANSFER_SCOPED')

    def test_added_six_wire_type_aliases_are_rejected(self):
        for name, reason, changed, additional in mutations(self.raw):
            if additional:
                with self.subTest(control=name):
                    with self.assertRaisesRegex(ValueError, reason):
                        audit_v2.audit(changed, self.fixtures)

    def test_original_eight_corruptions_still_reject_for_their_reason(self):
        for name, reason, changed, additional in mutations(self.raw):
            if not additional:
                with self.subTest(control=name):
                    with self.assertRaisesRegex(ValueError, reason):
                        audit_v2.audit(changed, self.fixtures)


if __name__ == '__main__':
    unittest.main()
