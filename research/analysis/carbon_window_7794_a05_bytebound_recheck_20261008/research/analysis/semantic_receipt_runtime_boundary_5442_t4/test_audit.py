from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import audit

RAW = Path(__file__).parent / "raw" / "probe.json"


class AuditTests(unittest.TestCase):
    def test_frozen_raw_is_accepted(self):
        with contextlib.redirect_stdout(io.StringIO()):
            audit.main(str(RAW))

    def test_mutations_reject(self):
        baseline = json.loads(RAW.read_text(encoding="utf-8"))
        mutations = (
            ("outcome", lambda row: row.update(outcome={"stage": "verified", "effect_verified": False, "release_verified": True})),
            ("intent_field", lambda row: row["effect_receipt_fields"].append("intent_hash")),
            ("source_blob", lambda row: row["source_blobs"].update({"runtime/kernel/contracts.py": "0" * 40})),
            ("scope", lambda row: row.update(scope="semantic success proved")),
        )
        for name, mutate in mutations:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                row = json.loads(json.dumps(baseline))
                mutate(row)
                raw = Path(temporary) / "mutated.json"
                raw.write_text(json.dumps(row), encoding="utf-8")
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit) as caught:
                        audit.main(str(raw))
                self.assertEqual(caught.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
