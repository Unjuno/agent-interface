import json
from pathlib import Path
import tempfile
import unittest

import auditor_effect_v4 as auditor


class AuditCorrectionTests(unittest.TestCase):
    def test_transport_control_is_enforced_even_when_raw_reads_are_valid(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "mcp-responses").mkdir()
            session = "session-04"
            calls = []
            reads = []
            for i in range(6):
                call_id = f"call-{i}"
                name = f"retained-{i}.json"
                receipt = {"call_id": call_id, "retained_call": {"state": "finished"},
                           "operation_invoked": False}
                raw = json.dumps({"content": [{"type": "text", "text": json.dumps(receipt)}]})
                (root / "mcp-responses" / name).write_text(raw, encoding="utf-8")
                calls.append({"label": f"label-{i}", "payload": {"call_id": call_id},
                              "retained_response_file": name})
                reads.append({"source_label": f"label-{i}", "state": "finished",
                              "operation_invoked": False, "session_id": session})
            trace = {"session_id": session, "calls": calls, "retained_reads": reads,
                     "retained_transport": {"scope": "single-public-stdio-client-session",
                         "session_id": session, "same_client_context": True, "read_count": 6}}
            bundle = {"trace": trace, "bundle_path": str(root)}
            self.assertTrue(auditor.retained_binding_valid(bundle))
            trace["retained_transport"]["same_client_context"] = False
            self.assertFalse(auditor.retained_binding_valid(bundle))
            trace["retained_transport"]["same_client_context"] = True
            trace["calls"][0]["payload"]["call_id"] = "different-call"
            self.assertFalse(auditor.retained_binding_valid(bundle))


if __name__ == "__main__":
    unittest.main()

