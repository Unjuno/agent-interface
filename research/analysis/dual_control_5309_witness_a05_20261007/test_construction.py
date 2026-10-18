import json
import unittest
from pathlib import Path

import candidate
import auditor

ROOT=Path(__file__).resolve().parent


class ConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=json.loads((ROOT/"fixture.json").read_text())
        cls.raw=candidate.run(cls.fixture)

    def row(self,scenario,arm,state="hidden-a"):
        return next(r for r in self.raw["rows"] if (r["scenario"],r["arm"],r["state"])==(scenario,arm,state))

    def test_primary_generic_loses_witness_but_witness_aware_completes(self):
        generic=self.row("primary","GENERIC_IG")
        aware=self.row("primary","WITNESS_AWARE")
        self.assertEqual(generic["decision"],"UNKNOWN_EFFECT_WITNESS_LOST")
        self.assertEqual(aware["decision"],"COMPLETE")
        self.assertFalse(generic["completed"])
        self.assertTrue(aware["completed"])

    def test_identical_admissible_set(self):
        for scenario in ("primary","witness-irrelevant"):
            generic=self.row(scenario,"GENERIC_IG")
            aware=self.row(scenario,"WITNESS_AWARE")
            self.assertEqual(generic["admitted_action_set"],aware["admitted_action_set"])
            self.assertEqual(generic["admitted_action_set"],self.fixture["actions"]["generic_ig"])
        self.assertEqual(self.row("witness-irrelevant","WITNESS_AWARE")["decision"],"COMPLETE")

    def test_no_path_stale_duplicate_stop_controls(self):
        self.assertEqual(self.row("no-safe-path","WITNESS_AWARE")["decision"],"UNKNOWN")
        self.assertEqual(self.row("stale-receipt","WITNESS_AWARE")["decision"],"UNKNOWN")
        self.assertEqual(self.row("duplicate-receipt","WITNESS_AWARE")["decision"],"COMPLETE")
        self.assertEqual(self.row("urgent-stop","WITNESS_AWARE")["decision"],"STOP_AND_RELEASE")
        self.assertEqual(self.row("misspecified-model","WITNESS_AWARE")["decision"],"UNKNOWN_MODEL_MISMATCH")

    def test_all_rows_have_zero_authority_and_reconstruct(self):
        self.assertEqual(len(self.raw["rows"]),56)
        self.assertTrue(all(r["authority_grants"]==0 for r in self.raw["rows"]))
        self.assertEqual(auditor.audit(self.fixture,self.raw)["rows"],56)

    def test_auditor_rejects_mutations(self):
        for mutate in (
            lambda r:r["rows"][0].update(authority_grants=1),
            lambda r:r["rows"][0].update(completed=True),
            lambda r:next(x for x in r["rows"] if x["scenario"]=="primary" and x["arm"]=="GENERIC_IG").update(decision="COMPLETE",completed=True),
            lambda r:r["rows"].pop(),
            lambda r:r["rows"].append(dict(r["rows"][0])),
            lambda r:next(x for x in r["rows"] if x["scenario"]=="urgent-stop").update(decision="COMPLETE",completed=True),
        ):
            corrupted=json.loads(json.dumps(self.raw))
            mutate(corrupted)
            with self.assertRaises(ValueError):auditor.audit(self.fixture,corrupted)


if __name__=="__main__":unittest.main()
