import json
import unittest
from types import SimpleNamespace

from auditor_v2 import normalize_receipts
from runner_v2 import normalize_public_receipt


def public_response():
    raw = {"schema": "agent-interface/runtime-observation-v1",
           "observation_id": "obs-1", "status": "returned",
           "input_dispatched": False, "side_effect_authority": False,
           "session": {"session_id": "session-1", "state": "open"}}
    text = {"schema": "agent-interface/review-v1",
            "receipt": {"schema": "agent-interface/receipt-view-v1",
                        "authority": "none",
                        "report": {"schema": raw["schema"], "status": "returned"},
                        "source": {"raw_report": raw}},
            "session": raw["session"], "call_id": "call-1",
            "call_directory": "/evidence/call-1"}
    return text


class ReceiptProjectionTests(unittest.TestCase):
    def test_runner_projects_nested_status_without_changing_raw_schema(self):
        text = json.dumps(public_response())
        result = SimpleNamespace(content=[SimpleNamespace(type="text", text=text)])
        normalized = normalize_public_receipt(result)
        self.assertEqual(normalized["schema"], "agent-interface/review-v1")
        self.assertEqual(normalized["status"], "returned")
        self.assertEqual(normalized["observation"]["observation_id"], "obs-1")
        self.assertFalse(normalized["input_dispatched"])
        self.assertFalse(normalized["side_effect_authority"])

    def test_auditor_projection_preserves_outer_raw_text_and_maps_capture(self):
        original = json.dumps(public_response())
        bundle = {"messages": {"response": {"json": {"content": [
                    {"type": "text", "text": original}]}}},
                  "reports": {"call-1": {"status": "returned", "session": {"session_id": "session-1"},
                     "observation": {"target": "inkscape", "native_window_id": 12}}}}
        normalized = normalize_receipts(bundle)
        text = normalized["messages"]["response"]["json"]["content"][0]["text"]
        payload = json.loads(text)
        self.assertEqual(payload["receipt"]["source"]["raw_report"]["observation_id"], "obs-1")
        self.assertEqual(payload["status"], "returned")
        report = normalized["reports"]["call-1"]
        self.assertEqual(report["observation"]["status"], "returned")
        self.assertEqual(report["observation"]["observation"]["target"], "inkscape")
        self.assertEqual(json.loads(original)["schema"], "agent-interface/review-v1")

    def test_unknown_receipt_schema_fails_closed(self):
        text = public_response()
        text["receipt"]["schema"] = "agent-interface/receipt-view-v9"
        result = SimpleNamespace(content=[SimpleNamespace(type="text", text=json.dumps(text))])
        with self.assertRaises(AssertionError):
            normalize_public_receipt(result)


if __name__ == "__main__":
    unittest.main()
