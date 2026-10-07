import json
import unittest
from pathlib import Path
from candidate import build
from audit import audit_without_mutations, audit

ROOT=Path(__file__).parent
FIXTURE=(ROOT/"fixture.json").read_bytes()
RAW=build(FIXTURE)

class ConstructionTests(unittest.TestCase):
    def test_denominator_and_depths(self):
        self.assertEqual(len(RAW["rows"]),32)
        self.assertEqual({r["depth"] for r in RAW["rows"]},{0,1,4,8})
    def test_current_truth_is_fixed_within_stratum(self):
        for c in ("Q_CURRENT_VALID","Q_CHANGE_HISTORY_REQUIRED"):
            for d in (0,1,4,8):
                rows=[r for r in RAW["rows"] if r["condition_id"]==c and r["depth"]==d]
                self.assertEqual(len({json.dumps(r["body"]["current"],sort_keys=True) for r in rows}),1)
    def test_history_required_baseline_survives_every_arm(self):
        for r in RAW["rows"]:
            if r["kind"]=="history_required":
                self.assertEqual(r["body"]["baseline"]["value"],"TARGET_A")
                self.assertIn("TARGET_A",r["body"]["query"])
                self.assertIn("TARGET_Z",r["body"]["query"])
    def test_nonconflicting_control_has_equal_count(self):
        for d in (0,1,4,8):
            r=next(x for x in RAW["rows"] if x["condition_id"]=="Q_CURRENT_VALID" and x["depth"]==d and x["arm"]=="NONCONFLICTING_HISTORY")
            self.assertEqual(len(r["body"]["episodes"]),d)
    def test_source_linked_ledger_has_lineage(self):
        rows=[r for r in RAW["rows"] if r["arm"]=="SOURCE_LINKED_DELTA" and r["depth"]==4]
        self.assertTrue(all(len(r["body"]["ledger"])==4 for r in rows))
    def test_ledger_never_has_execution_authority(self):
        self.assertTrue(all(r["body"]["authority"]["execution_authority"] is False for r in RAW["rows"]))
    def test_auditor_accepts_unmodified_raw_and_rejects_four_controls(self):
        result=audit(FIXTURE,RAW)
        self.assertEqual(result["errors"],[])
        self.assertEqual(result["status"],"PASS_FIXTURE_METHOD_SCOPED")
        self.assertTrue(all(item["rejected"] for item in result["mutation_checks"]))
    def test_only_position_control_moves_current_cue(self):
        self.assertTrue(RAW["position_control"]["offset_differs"])
    def test_cue_offset_is_shared_within_matched_groups(self):
        for c in ("Q_CURRENT_VALID","Q_CHANGE_HISTORY_REQUIRED"):
            for d in (0,1,4,8):
                self.assertEqual(len({r["current_cue_byte_offset"] for r in RAW["rows"] if r["condition_id"]==c and r["depth"]==d}),1)
    def test_exact_utf8_bytes_match_within_strata(self):
        for c in ("Q_CURRENT_VALID","Q_CHANGE_HISTORY_REQUIRED"):
            for d in (0,1,4,8):
                self.assertEqual(len({r["utf8_bytes"] for r in RAW["rows"] if r["condition_id"]==c and r["depth"]==d}),1)

if __name__=="__main__": unittest.main()
