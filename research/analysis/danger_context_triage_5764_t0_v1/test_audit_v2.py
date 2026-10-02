import unittest

from audit_v2 import frozen_stream_hash


class AuditV2AdapterTests(unittest.TestCase):
    def test_reads_stream_digest_from_frozen_fixture_object(self):
        digest = "a" * 64
        frozen = {"fixture": {"stream_sha256": digest}}
        self.assertEqual(frozen_stream_hash(frozen), digest)

    def test_missing_frozen_stream_digest_fails_closed(self):
        with self.assertRaises((KeyError, ValueError)):
            frozen_stream_hash({"fixture": {}})


if __name__ == "__main__":
    unittest.main()
