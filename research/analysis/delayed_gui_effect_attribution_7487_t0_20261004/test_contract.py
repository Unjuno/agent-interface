import json
import unittest
from pathlib import Path

import auditor
import candidate


class ContractTests(unittest.TestCase):
    def test_twenty_fact_preserving_presentations_and_six_mutations(self):
        ledger = json.loads((Path(__file__).parent / "frozen_ledger.json").read_text())
        records = [candidate.render(c, d, f) for c in ledger["cases"]
                   for d in candidate.DELAYS for f in candidate.FORMATS]
        self.assertEqual(len(records), 20)
        self.assertEqual(auditor.audit_records(ledger, records), [])
        tested = auditor.controls(ledger, records)
        self.assertEqual(sum(v for k, v in tested.items() if k != "unknown_not_relabelled"), 6)
        self.assertTrue(tested["unknown_not_relabelled"])
        unknown = next(r for r in records if r["case_id"] == "unknown_conflicting_provenance" and r["presentation"] == "SOURCE_BOUND_RECEIPT")
        effect = next(e for e in unknown["events"] if e["kind"] == "effect")
        self.assertEqual((effect["causal_link_status"], effect["source_action_id"], effect["source_actor"]), ("UNKNOWN", None, "UNKNOWN"))
        self.assertEqual({r["display_delay_ms"] for r in records}, {300, 1500})
        self.assertEqual({r["presentation"] for r in records}, set(candidate.FORMATS))
        for case in ledger["cases"]:
            case_rows = [r for r in records if r["case_id"] == case["case_id"]]
            for delay in (300, 1500):
                summary = next(r for r in case_rows if r["display_delay_ms"] == delay and r["presentation"] == "CHRONOLOGICAL_SUMMARY")
                receipt = next(r for r in case_rows if r["display_delay_ms"] == delay and r["presentation"] == "SOURCE_BOUND_RECEIPT")
                self.assertEqual(summary["effect_display_at_ms"], receipt["effect_display_at_ms"])
                self.assertEqual([{k: v for k, v in e.items() if k not in {"causal_link_status", "source_action_id", "source_actor", "evidence_id"}} for e in summary["events"]],
                                 [{k: v for k, v in e.items() if k not in {"causal_link_status", "source_action_id", "source_actor", "evidence_id"}} for e in receipt["events"]])


if __name__ == "__main__":
    unittest.main()
