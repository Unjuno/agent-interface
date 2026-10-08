from __future__ import annotations

import unittest

from measure import IMAGE_DIGEST, LOCAL_IMAGE_ID, digest_gate_passes


class DigestGateTests(unittest.TestCase):
    def test_image_table_separate_columns_is_accepted(self) -> None:
        table = (
            "REPOSITORY TAG DIGEST IMAGE ID\n"
            f"python 3.12-slim {IMAGE_DIGEST} {LOCAL_IMAGE_ID}\n"
        )
        self.assertTrue(digest_gate_passes(table))

    def test_wrong_digest_is_rejected(self) -> None:
        self.assertFalse(digest_gate_passes(f"python 3.12-slim sha256:{'0' * 64} {LOCAL_IMAGE_ID}"))

    def test_wrong_local_image_id_is_rejected(self) -> None:
        self.assertFalse(digest_gate_passes(f"python 3.12-slim {IMAGE_DIGEST} sha256:{'0' * 64}"))


if __name__ == "__main__":
    unittest.main()
