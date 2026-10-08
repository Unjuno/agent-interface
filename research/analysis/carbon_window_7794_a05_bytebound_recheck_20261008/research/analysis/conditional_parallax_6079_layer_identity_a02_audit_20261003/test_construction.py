"""A02 construction checks use private mini-records, never the A01 fixture/raw."""
from __future__ import annotations

import unittest

import audit_successor as audit


class AuditConstructionTests(unittest.TestCase):
    def test_hash_mismatch_is_typed_and_nonrecursive(self):
        with self.assertRaisesRegex(ValueError, "public_hash_mismatch"):
            audit.reconcile({}, {}, [], "not-the-hash")

    def test_exact_row_count_is_typed(self):
        public = {"cases": [{"case_id": f"c{i}"} for i in range(8)]}
        truth = {"cases": {f"c{i}": {} for i in range(8)}}
        canonical = (audit.json.dumps(public, sort_keys=True, separators=(",", ":")) + "\n").encode()
        digest = audit.hashlib.sha256(canonical).hexdigest()
        with self.assertRaisesRegex(ValueError, "exact_row_count_mismatch"):
            audit.reconcile(public, truth, [], digest)

    def test_raw_reconstruction_mismatch_is_typed(self):
        self.assertFalse(audit.require_reason({}, {}, [], "unused",
                                              "independent_raw_reconstruction_mismatch"))


if __name__ == "__main__":
    unittest.main()
