from __future__ import annotations

import unittest

from candidate import EXPECTED_SOURCE_BLOB, git_blob_sha1, probe_rows
from audit import parse_object_stream


class WriterReproductionConstructionTests(unittest.TestCase):
    def test_source_pin_is_a_git_blob_identity(self) -> None:
        self.assertEqual(git_blob_sha1(b""), "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")
        self.assertEqual(len(EXPECTED_SOURCE_BLOB), 40)

    def test_payload_has_embedded_newline_and_terminal_order(self) -> None:
        rows = probe_rows()
        self.assertEqual([row["event"] for row in rows], ["probe", "terminal"])
        self.assertEqual(rows[0]["text"], "embedded\nvalue")

    def test_structural_parser_round_trips_literal_delimiter(self) -> None:
        raw = b'{"event":"probe","text":"embedded\\nvalue"}\\n{"event":"terminal"}\\n'
        rows = parse_object_stream(raw)
        self.assertEqual([row["event"] for row in rows], ["probe", "terminal"])
        self.assertEqual(rows[0]["text"], "embedded\nvalue")


if __name__ == "__main__":
    unittest.main()
