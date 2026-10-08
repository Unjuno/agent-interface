import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
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
        for kind in ("leak_seed","confound_density","wrong_identity","wrong_presence_class","drop_fixture","authority_inflation","identity_payload_mismatch"):
            self.assertTrue(auditor.mutation_rejected(raw,SPEC,kind),kind)

    def test_auditor_binds_allocation_and_fixture_id_to_row_payload(self):
        raw=candidate.build(SPEC)
        changed=dict(raw)
        changed["allocation"]="another-allocation"
        with self.assertRaises(ValueError):
            auditor.check(changed,SPEC)
        changed=dict(raw)
        changed["rows"]=list(raw["rows"])
        changed["rows"][0]=dict(raw["rows"][0],spacing_px=999)
        with self.assertRaises(ValueError):
            auditor.check(changed,SPEC)

    def _run_wrapper_in_fresh_directory(self, wrapper_name, role_stub, seed_candidate=False):
        with tempfile.TemporaryDirectory() as temp:
            package=Path(temp)/"package"
            package.mkdir()
            shutil.copy2(ROOT/wrapper_name,package/wrapper_name)
            (package/"spec.json").write_text("{}\n")
            (package/("candidate.py" if wrapper_name=="run_candidate_once.sh" else "auditor.py")).write_text(role_stub)
            if seed_candidate:
                results=package/"results"
                results.mkdir()
                (results/"candidate.exit").write_text("0\n")
                (results/"candidate.raw.json").write_text("{}\n")
            first=subprocess.run(["sh",str(package/wrapper_name)],cwd=temp, capture_output=True,text=True)
            self.assertEqual(first.returncode,0,first.stderr)
            results=package/"results"
            self.assertTrue((results/"candidate.started" if wrapper_name=="run_candidate_once.sh" else results/"auditor.started").is_file())
            self.assertTrue((results/"candidate.exit" if wrapper_name=="run_candidate_once.sh" else results/"auditor.exit").is_file())
            self.assertTrue((results/"candidate.stdout.txt" if wrapper_name=="run_candidate_once.sh" else results/"auditor.stdout.txt").read_text().strip())
            second=subprocess.run(["sh",str(package/wrapper_name)],cwd=temp,capture_output=True,text=True)
            self.assertEqual(second.returncode,75)

    def test_candidate_wrapper_creates_results_before_redirection_and_refuses_retry(self):
        stub='import argparse\nfrom pathlib import Path\np=argparse.ArgumentParser(); p.add_argument("--spec"); p.add_argument("--output"); a=p.parse_args(); Path(a.output).write_text("{}\\n"); print("candidate stub")\n'
        self._run_wrapper_in_fresh_directory("run_candidate_once.sh",stub)

    def test_auditor_wrapper_requires_candidate_and_refuses_retry(self):
        stub='import argparse\nfrom pathlib import Path\np=argparse.ArgumentParser(); p.add_argument("--spec"); p.add_argument("--raw"); p.add_argument("--output"); a=p.parse_args(); Path(a.output).write_text("{}\\n"); print("auditor stub")\n'
        self._run_wrapper_in_fresh_directory("run_auditor_once.sh",stub,seed_candidate=True)

if __name__=="__main__": unittest.main()
