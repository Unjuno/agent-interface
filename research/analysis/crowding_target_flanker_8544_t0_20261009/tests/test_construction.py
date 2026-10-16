import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/f"{name}.py")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

candidate=load("candidate")
auditor=load("auditor")
SPEC=json.loads((ROOT/"spec.json").read_text())

class ConstructionTests(unittest.TestCase):
    def test_all_endpoint_templates_score_separately(self):
        raw=candidate.build(SPEC)
        result=auditor.check(raw,SPEC)
        self.assertEqual(result["fixtures"],5632)
        self.assertEqual(result["errors"],0)
        self.assertEqual(result["split_seeds"],{"development":[0,1,2,3,4,5],"held_out":[6,7]})

    def test_neighbor_substitution_preserves_detection(self):
        wrong={"status":"found","identity":"neighbor","point":[610,380],"schema_valid":True}
        self.assertEqual(auditor.score(wrong,True),"neighbor_substitution")
        self.assertNotEqual(auditor.score(wrong,True),"miss")

    def test_malformed_and_ambiguous_outputs_are_not_absorbed(self):
        self.assertEqual(auditor.score({"status":"found","identity":"target","point":[520,380],"schema_valid":False},True),"schema_error")
        self.assertEqual(auditor.score({"status":"found","identity":"target_or_neighbor","point":[565,380],"schema_valid":True},True),"ambiguous_identity")

    def test_paired_cells_cross_spacing_and_eccentricity_at_constant_density(self):
        raw=candidate.build(SPEC)
        audit=auditor.check(raw,SPEC)
        self.assertEqual(audit["factor_strata"],128)
        self.assertEqual({r["global_control_count"] for r in raw["rows"]},{4})

    def test_split_leakage_and_density_alias_mutations_rejected(self):
        raw=candidate.build(SPEC)
        for kind in ("leak_seed","confound_density","wrong_identity","wrong_presence_class","drop_fixture","authority_inflation"):
            self.assertTrue(auditor.mutation_rejected(raw,SPEC,kind),kind)

if __name__=="__main__": unittest.main()
