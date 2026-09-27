from __future__ import annotations

import hashlib
import unittest

from independent_audit_v2 import byte_binding_errors


class ByteBindingTests(unittest.TestCase):
    def setUp(self):
        self.raw = b"{\"rows\":1}\n"
        self.audit = b"{\"status\":\"PASS\"}\n"
        self.binding = {
            "artifact_raw_sha256": hashlib.sha256(self.raw).hexdigest(),
            "artifact_audit_sha256": hashlib.sha256(self.audit).hexdigest(),
        }

    def test_exact_bytes_match(self):
        self.assertEqual(byte_binding_errors(self.raw, self.audit, self.binding), [])

    def test_raw_trailing_newline_is_rejected(self):
        self.assertEqual(
            byte_binding_errors(self.raw + b"\n", self.audit, self.binding),
            ["artifact_raw_sha256_mismatch"],
        )

    def test_audit_trailing_newline_is_rejected(self):
        self.assertEqual(
            byte_binding_errors(self.raw, self.audit + b"\n", self.binding),
            ["artifact_audit_sha256_mismatch"],
        )

    def test_missing_binding_digest_fails_closed(self):
        self.assertEqual(
            byte_binding_errors(self.raw, self.audit, {}),
            ["artifact_raw_sha256_mismatch", "artifact_audit_sha256_mismatch"],
        )


if __name__ == "__main__":
    unittest.main()
