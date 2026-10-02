from __future__ import annotations

import unittest

from audit_trace import parse_object_stream


class ParseObjectStreamTests(unittest.TestCase):
    def test_normal_jsonl(self) -> None:
        rows, kind = parse_object_stream(b'{"event":"a"}\n{"event":"b"}\n')
        self.assertEqual([row["event"] for row in rows], ["a", "b"])
        self.assertEqual(kind, "JSONL")

    def test_literal_delimiters_and_escaped_string_newline(self) -> None:
        raw = b'{"event":"a","text":"inside\\nvalue"}\\n{"event":"b"}'
        rows, kind = parse_object_stream(raw)
        self.assertEqual([row["event"] for row in rows], ["a", "b"])
        self.assertEqual(rows[0]["text"], "inside\nvalue")
        self.assertEqual(kind, "OBJECT_STREAM_WITH_ESCAPED_NEWLINE_DELIMITERS")

    def test_rejects_truncated_object(self) -> None:
        with self.assertRaises(ValueError):
            parse_object_stream(b'{"event":"a"}\\n{"event":')

    def test_rejects_non_object_event(self) -> None:
        with self.assertRaises(ValueError):
            parse_object_stream(b'{"event":"a"}\\n[]')

    def test_rejects_empty_stream(self) -> None:
        with self.assertRaises(ValueError):
            parse_object_stream(b" \r\n ")


if __name__ == "__main__":
    unittest.main()
