import copy
import json
from pathlib import Path
import tempfile
import unittest

from audit import audit
from candidate import execute


ROOT = Path(__file__).parent
SPEC = json.loads((ROOT / "scenarios.json").read_text(encoding="utf-8"))


class ClaimLadderTests(unittest.TestCase):
    def test_partial_positive_never_becomes_claim_ladder_allow(self):
        scenario = next(s for s in SPEC["scenarios"] if s["id"] == "partial_positive_after_identity")
        row = execute(scenario, "CLAIM_LADDER", SPEC)
        self.assertEqual(row["disposition"], "PARTIAL_UNKNOWN")
        self.assertEqual(row["consumer_side_effects"], 0)

    def test_decisive_negative_is_logically_earlier_than_all_or_nothing(self):
        scenario = next(s for s in SPEC["scenarios"] if s["id"] == "decisive_identity_negative")
        ladder = execute(scenario, "CLAIM_LADDER", SPEC)
        baseline = execute(scenario, "ALL_OR_NOTHING_TIMEOUT", SPEC)
        self.assertEqual((ladder["disposition"], ladder["decision_ms"]), ("COUNTEREXAMPLE", 1))
        self.assertEqual((baseline["disposition"], baseline["decision_ms"]), ("COUNTEREXAMPLE", 11))

    def test_later_same_generation_contradiction_fails_closed(self):
        scenario = next(s for s in SPEC["scenarios"] if s["id"] == "contradictory_same_generation")
        self.assertEqual(execute(scenario, "CLAIM_LADDER", SPEC)["disposition"], "PARTIAL_UNKNOWN")

    def test_torn_receipt_is_not_coverage_and_durable_replay_is_deduped(self):
        torn = next(s for s in SPEC["scenarios"] if s["id"] == "torn_receipt_before_durable")
        recovered = next(s for s in SPEC["scenarios"] if s["id"] == "duplicate_recovery_replay")
        self.assertEqual(execute(torn, "CLAIM_LADDER", SPEC)["disposition"], "PARTIAL_UNKNOWN")
        replay = execute(recovered, "CLAIM_LADDER", SPEC)
        self.assertEqual(replay["disposition"], "COMPLETE_VERDICT")
        self.assertEqual(replay["recovery_replays"], 6)
        self.assertEqual(replay["final_commit_count"], 1)

    def test_all_rows_reconstruct_and_mutations_reject(self):
        rows = [execute(s, p, SPEC) for s in SPEC["scenarios"] for p in SPEC["policies"]]
        raw = {"schema":"claim-scoped-verdict-raw-v1", "spec_sha256":"", "scenario_count":15,
               "policies":SPEC["policies"], "rows":rows, "row_count":len(rows)}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            original_hash = __import__("hashlib").sha256((ROOT / "scenarios.json").read_bytes()).hexdigest()
            raw["spec_sha256"] = original_hash
            path.write_text(json.dumps(raw), encoding="utf-8")
            result = audit(ROOT / "scenarios.json", path)
            self.assertEqual(result["status"], "PASS_METHOD_SCOPED", result["errors"])
            for mutate in (
                lambda r: r["rows"].pop(),
                lambda r: r["rows"][2].update(disposition="ALLOW"),
                lambda r: r["rows"][27].update(consumer_side_effects=1),
                lambda r: r["rows"][28].update(recovery_replays=99),
            ):
                damaged = copy.deepcopy(raw)
                mutate(damaged)
                path.write_text(json.dumps(damaged), encoding="utf-8")
                self.assertNotEqual(audit(ROOT / "scenarios.json", path)["status"], "PASS_METHOD_SCOPED")


if __name__ == "__main__":
    unittest.main()
