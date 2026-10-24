"""P09 redaction must preserve raw-ledger bytes and nested JSON validity."""
import json
from pathlib import Path
import tempfile
import unittest

from research.integration.current_main_appserver_matched_efficiency_20261025_p09.privacy_redact import redact_run

class PrivacyRedactionTests(unittest.TestCase):
    def test_raw_binary_ledger_is_immutable_and_nested_json_is_scrubbed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = root / "ledger" / "raw" / "provider-response.bin"
            raw.parent.mkdir(parents=True)
            raw_bytes = b'{"secret_path":"C:\\\\Users\\\\alice\\\\private.txt"}'
            raw.write_bytes(raw_bytes)
            envelope = root / "envelope.json"
            envelope.write_text(json.dumps({"text": json.dumps({"path":r"C:\Users\alice\file.txt"})}), encoding="utf-8")
            report = redact_run(root)
            self.assertEqual(raw.read_bytes(), raw_bytes)
            scrubbed = json.loads(envelope.read_text(encoding="utf-8"))
            nested = json.loads(scrubbed["text"])
            self.assertEqual(nested["path"], "<private-path>")
            self.assertEqual(len(report["redactions"]), 1)

if __name__ == "__main__":
    unittest.main()
