import json
from pathlib import Path
import tempfile
import unittest

import auditor_effect_v3 as audit


class RetainedReadBindingTests(unittest.TestCase):
    def test_binds_six_noop_reads_by_call_id_to_one_client_session(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "mcp-responses").mkdir()
            session = "session-a"
            calls = []
            for i in range(6):
                call_id = f"call-{i}"
                label = f"retained-{i}.json"
                payload = {"call_id": call_id, "retained_call": {"state": "finished"},
                           "operation_invoked": False}
                outer = {"content": [{"type": "text", "text": json.dumps(payload)}]}
                (root / "mcp-responses" / label).write_text(json.dumps(outer), encoding="utf-8")
                calls.append({"payload": {"call_id": call_id}, "retained_response_file": label,
                              "session_id": session})
            reads = [{"source_label": f"label-{i}", "session_id": session,
                      "state": "finished", "operation_invoked": False} for i in range(6)]
            for i, call in enumerate(calls):
                call["label"] = f"label-{i}"
            trace = {"session_id": session, "calls": calls, "retained_reads": reads, "retained_transport": {
                "scope": "single-public-stdio-client-session", "same_client_context": True,
                "session_id": session, "read_count": 6}}
            self.assertTrue(audit.retained_reads_valid({"trace": trace, "bundle_path": directory}))
            trace["calls"][3]["payload"]["call_id"] = "wrong-call"
            self.assertFalse(audit.retained_reads_valid({"trace": trace, "bundle_path": directory}))
            trace["calls"][3]["payload"]["call_id"] = "call-3"
            trace["retained_transport"]["same_client_context"] = False
            self.assertFalse(audit.retained_reads_valid({"trace": trace, "bundle_path": directory}))


if __name__ == "__main__":
    unittest.main()

