"""Connect the public v3 G10-shaped caller result to the Issue #57 ledger.

The X11 bridge and task observations are fakes, and the independent scorer
uses the retained historical FODS fixture. This checks result/evidence shape
and custody, not a fresh Calc effect or a live comparison allocation.
"""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from research.integration.test_calc_g10_caller_score_v1 import (
    G10CallerCompositionTests,
    ROOT,
)
from research.live_control.issue57_v3_attempt_ledger_v1 import (
    AppendOnlyAttemptLedger,
    make_row,
)


class Issue57V3G10CompositionTests(unittest.TestCase):
    def test_public_caller_score_release_and_raw_join_in_append_only_ledger(self):
        bridge, calls, result = G10CallerCompositionTests().run_case()
        self.assertEqual(result["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(result["route"], "reuse")
        self.assertEqual(result["task_effect"], "succeeded")
        self.assertEqual(result["effect_receipt"]["status"], "succeeded")
        self.assertEqual(calls["verify"], 1)

        receipt = result["compiled_execution_receipt"]
        terminals = [event for event in receipt["critical_events"]
                     if event.get("event") == "action_terminal"]
        self.assertEqual(len(terminals), receipt["completed_transitions"])
        self.assertTrue(terminals)
        self.assertTrue(all(event.get("release_verified") is True
                            for event in terminals))
        receipt_bytes = (json.dumps(receipt, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False) + "\n").encode("utf-8")
        release = {"status": "succeeded", "verified": True,
            "keys_down": [], "buttons_down": [],
            "evidence_ref": "compiled-execution-receipt",
            "evidence_digest": hashlib.sha256(receipt_bytes).hexdigest()}
        raw = ROOT / "runs" / "compiled_ocrlive10" / "second.fods"
        self.assertTrue(raw.is_file())
        expected_raw_digest = hashlib.sha256(raw.read_bytes()).hexdigest()
        self.assertEqual(result["effect_receipt"]["evidence_digest"],
                         expected_raw_digest)

        with tempfile.TemporaryDirectory(prefix="issue57-v3-g10-ledger-") as tmp:
            ledger = AppendOnlyAttemptLedger(Path(tmp) / "attempts.jsonl",
                                             ["g10-persistent-task-2"])
            row = make_row("g10-persistent-task-2", result, release,
                           result["effect_receipt"], raw_paths=(raw,))
            ledger.append(row)
            audit = ledger.audit()

        self.assertEqual(audit["rows"], 1)
        self.assertEqual(audit["attempts"], 0)
        self.assertEqual(row["compiled_execution_receipt"], receipt)
        self.assertEqual(row["effect_receipt"], result["effect_receipt"])
        self.assertEqual(row["raw_evidence"], [{"name": raw.name,
            "size_bytes": raw.stat().st_size, "sha256": expected_raw_digest}])
        self.assertEqual(len(bridge.inputs), 2)


if __name__ == "__main__":
    unittest.main()
