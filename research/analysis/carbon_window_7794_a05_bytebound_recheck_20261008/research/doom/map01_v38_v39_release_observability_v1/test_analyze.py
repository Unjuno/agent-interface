import json
import unittest
from copy import deepcopy
from pathlib import Path

import analyze


class ReleaseObservabilityConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v38 = analyze.read_jsonl(analyze.V38)
        cls.v39 = analyze.read_jsonl(analyze.V39)

    def test_selected_trace_has_two_compliant_hypotheses(self):
        result = analyze.derive(deepcopy(self.v38), deepcopy(self.v39))
        self.assertEqual(result["status"], "NON_IDENTIFIABLE_FROM_RETAINED_RELEASE_TELEMETRY")
        self.assertEqual(result["observed"]["ack_to_outer_completion_ms"], 565.474663)
        self.assertEqual(result["distinct_candidate_separation_ms"], 150.0)

    def test_missing_acknowledgement_stops(self):
        v39 = [row for row in deepcopy(self.v39)
               if not (row.get("event") == "keys_held" and row.get("id") == "cover-1"
                       and row.get("step") == 0)]
        with self.assertRaisesRegex(analyze.StopAudit, "acknowledgement/completion"):
            analyze.derive(deepcopy(self.v38), v39)

    def test_inverted_completion_stops(self):
        v39 = deepcopy(self.v39)
        row = next(row for row in v39 if row.get("event") == "step_completed"
                   and row.get("id") == "cover-1" and row.get("step") == 0)
        row["completed_ns"] = 55511911802239
        with self.assertRaisesRegex(analyze.StopAudit, "two candidate releases"):
            analyze.derive(deepcopy(self.v38), v39)

    def test_changed_selected_command_stops(self):
        v39 = deepcopy(self.v39)
        row = next(row for row in v39 if row.get("event") == "command"
                   and row.get("command", {}).get("id") == "cover-1"
                   and row.get("command", {}).get("op") == "submit")
        row["command"]["steps"][0]["duration_ms"] = 700
        with self.assertRaisesRegex(analyze.StopAudit, "hold command differs"):
            analyze.derive(deepcopy(self.v38), v39)


if __name__ == "__main__":
    unittest.main()
