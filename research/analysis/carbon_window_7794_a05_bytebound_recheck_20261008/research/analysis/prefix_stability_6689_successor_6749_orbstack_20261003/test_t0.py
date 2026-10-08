"""Construction tests only; formal candidate/auditor counts are separate."""
import json
import unittest
from pathlib import Path
import candidate
import auditor

ROOT=Path(__file__).parent

class Construction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec=json.loads((ROOT/"fixture.json").read_text())
        cls.raw=candidate.build(cls.spec,ROOT/"fixture.json")

    def test_finite_coverage_and_separate_count_spaces(self):
        self.assertEqual(self.raw["world_count"],32)
        self.assertEqual(self.raw["trace_count"],len(auditor.legal_completions(self.spec)))
        self.assertTrue(set(self.raw["disposition_counts"]).issubset({"STABLE_FAIL","STABLE_PASS","STABLE_UNKNOWN","PROVISIONAL","CLOSED_FRONTIER_REQUIRED"}))
        self.assertTrue(all(k.startswith("EARLY_") for k in self.raw["early_finalization_metrics"]))

    def test_decisive_negative_keeps_unfinished_mandatory_obligations(self):
        witnesses=[r for r in self.raw["rows"] if r["classification"]=="STABLE_FAIL" and not r["terminal_prefix"]]
        self.assertTrue(witnesses)
        self.assertTrue(any(any(o.startswith("mandatory:") for o in r["pending_obligations"]) for r in witnesses))

    def test_positive_needs_complete_frontier(self):
        for row in self.raw["rows"]:
            if row["classification"]=="STABLE_PASS":
                s={(e["source"],e["type"]):e["value"] for e in row["prefix"]}
                self.assertTrue(all(s.get((x,"result"))=="PASS" for x in ("target","effect")))
                self.assertEqual(s.get(("generation","status")),"CURRENT")
                self.assertEqual(s.get(("optional","frontier")),"COMPLETE")

    def test_raw_only_oracle_and_all_five_mutations(self):
        self.assertEqual(auditor.audit(self.spec,self.raw,ROOT/"fixture.json"),[])
        for name in ("drop_pending_mandatory","mix_derived_metric","forge_complete","stale_as_current","timeout_as_complete"):
            with self.subTest(name=name):
                self.assertTrue(auditor.audit(self.spec,auditor.mutate(self.raw,name),ROOT/"fixture.json"))

    def test_no_authority_or_effect(self):
        self.assertEqual(self.raw["authority_grants"],0)
        self.assertEqual(self.raw["consumer_side_effects"],0)
        self.assertTrue(all(not r["consumer_authority"] and r["consumer_side_effects"]==0 for r in self.raw["rows"]))

if __name__=="__main__": unittest.main()
