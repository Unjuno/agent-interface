from __future__ import annotations

import gzip
import json
import tempfile
import unittest
from pathlib import Path

from audit import load_jsonl


class JsonlReaderTests(unittest.TestCase):
    def test_reads_plain_candidate_jsonl(self) -> None:
        rows = [{"case_id": "opaque-1", "value": 7}]
        payload = "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows)
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "candidate.jsonl"
            path.write_text(payload, encoding="utf-8", newline="\n")
            self.assertEqual(load_jsonl(path), rows)

    def test_reads_gzip_observer_jsonl(self) -> None:
        rows = [{"case_id": "opaque-2", "value": 11}]
        payload = "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows)
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "observer_input.jsonl.gz"
            with gzip.open(path, "wt", encoding="utf-8", newline="\n") as stream:
                stream.write(payload)
            self.assertEqual(load_jsonl(path), rows)


if __name__ == "__main__":
    unittest.main()
