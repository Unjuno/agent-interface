"""Construction-only tests. No model optimizer updates are performed here."""
import ast, base64, gzip, hashlib, json, pathlib, subprocess, sys, unittest

ROOT=pathlib.Path(__file__).resolve().parent
RUNNER=(ROOT/"runner.py").read_text(encoding="utf-8")
AUDIT=(ROOT/"audit.py").read_text(encoding="utf-8")

class FrozenContract(unittest.TestCase):
    def test_sources_parse(self):
        ast.parse(RUNNER);ast.parse(AUDIT)
    def test_frozen_seed_order_and_dimensions(self):
        for needle in ("SEEDS=(3451,3452,3453,3454,3455)","NBASE,NSUPPORT,NTEST=512,16,4096","BASE_STEPS,PER_FEEDBACK=400,8","seed+30","seed+(35 if name==\"legacy\" else 31)"):
            self.assertIn(needle,RUNNER)
        self.assertIn("ORDER={3451:(\"legacy\",\"shared\"),3452:(\"shared\",\"legacy\"),3453:(\"legacy\",\"shared\"),3454:(\"shared\",\"legacy\"),3455:(\"legacy\",\"shared\")}",RUNNER)
    def test_no_formal_invocation_in_construction_suite(self):
        self.assertNotIn("subprocess.run",RUNNER)
        self.assertNotIn("one_seed(",RUNNER[RUNNER.index("if __name__"):])
        self.assertNotIn("optimizer.step",RUNNER[RUNNER.index("if __name__"):])
    def test_auditor_is_independent_and_recomputes_rows(self):
        self.assertNotIn("import runner",AUDIT)
        for needle in ("torch.randn(4096,8","prediction_metric","curve_metric","identical_adapter_starts","roundtrip_exact","rollback_exact","PASS_SAMPLER_SEED_EXPLAINS_COLLAPSE_SCOPED"):
            self.assertIn(needle,AUDIT)
    def test_gate_constants_match_issue(self):
        for needle in ("legacy_mean>.10","all(x>=.90 for x in shared)","paired_mean>=.50","p95<=60","HOLD_LEGACY_COLLAPSE_NOT_REPRODUCED"):
            self.assertIn(needle,AUDIT)

    def test_auditor_accepts_fixture_and_rejects_mutations(self):
        # Small one-seed contract fixture: construction/audit only, not model training.
        seed=3451
        expected_by_seed={}
        expected_a_by_seed={}
        for current_seed in (3451,3452,3453,3454,3455):
            x=__import__("torch").randn(4096,8,generator=__import__("torch").Generator(device="cpu").manual_seed(current_seed+4))
            expected_by_seed[current_seed]=((1-(x[:,0]>0).long())*2+(x[:,1]>0).long()).tolist()
            xa=__import__("torch").randn(4096,8,generator=__import__("torch").Generator(device="cpu").manual_seed(current_seed+3))
            expected_a_by_seed[current_seed]=((xa[:,0]>0).long()*2+(xa[:,1]>0).long()).tolist()
        arms={}; timing={}; snapshots={}
        for arm in ("legacy","shared"):
            expected=expected_by_seed[seed]
            predictions=[];curves=[]
            for i in range(1,17):
                predictions.append({"arrival":i,"expected":expected,"predictions":expected,"correct":4096,"n":4096})
                curves.append({"feedback_seen":i,"correct":4096,"n":4096,"accuracy":1.0})
            arms[arm]={"decision":"PROPOSE","requested_role":arm,"epoch":1,"version":16,"selected_adapter":arm,"expected":expected,"predictions":expected,"correct":4096,"n":4096,"expected_b":expected,"curve":curves,"predictions_by_arrival":predictions}
            timing[arm]=[1.0]*16
            snapshots[arm]={"roundtrip_exact":True,"rollback_exact":True,"initial_sha256":"a"*64,"learned_sha256":"b"*64}
        rec={"seed":seed,"feedback_order":list(range(16)),"metrics":arms,"timing_ms":timing,"snapshots":snapshots,"base_immutable":True,"identical_adapter_starts":True,"initial_adapter_sha256":{"legacy":"c"*64,"shared":"c"*64},"invalid_routes":{"unknown_role":"YIELD","stale_epoch":"YIELD","wrong_version":"YIELD","missing_adapter":"YIELD"}}
        result={"allocation":"needle-lora-3441-rank4-minibatch-rng-paired-v1","environment":{"python":"3.11.9","torch":"2.5.1+cu121","cuda":"12.1","device":"NVIDIA GeForce RTX 3080 Laptop GPU","cublas_workspace_config":":4096:8","torch_threads":1,"deterministic":True},"seeds":[]}
        result["seeds"]=[dict(rec,seed=s,metrics={**{arm:{**value,"expected":expected_by_seed[s],"expected_b":expected_by_seed[s],"predictions":expected_by_seed[s],"correct":4096,"predictions_by_arrival":[{**row,"expected":expected_by_seed[s],"predictions":expected_by_seed[s]} for row in value["predictions_by_arrival"]]} for arm,value in arms.items()},"A":{"expected":expected_a_by_seed[s],"predictions":expected_a_by_seed[s],"correct":4096,"n":4096,"decision":"PROPOSE","requested_role":"A","version":0}},feedback_order=list(range(16)),initial_adapter_sha256={"legacy":"c"*64,"shared":"c"*64}) for s in (3451,3452,3453,3454,3455)]
        def invoke(obj,break_envelope=False):
            raw=json.dumps(obj,sort_keys=True,separators=(",",":")).encode()
            env={"sha256":("0"*64 if break_envelope else hashlib.sha256(raw).hexdigest()),"gzip_b64":base64.b64encode(gzip.compress(raw,mtime=0)).decode()}
            cp=subprocess.run([sys.executable,"-B","-c",AUDIT],input=json.dumps(env),text=True,capture_output=True,timeout=30)
            return cp
        good=invoke(result);self.assertEqual(good.returncode,0,msg=good.stdout+good.stderr);self.assertEqual(json.loads(good.stdout)["audit"],"PASS",msg=good.stdout)
        broken=invoke(result,True);self.assertNotEqual(broken.returncode,0);self.assertIn("STOP_RESULT_SHA256",broken.stderr)
        import copy
        mutated=copy.deepcopy(result);mutated["seeds"][0]["metrics"]["legacy"]["predictions"][0]=3
        out=invoke(mutated);self.assertEqual(json.loads(out.stdout)["audit"],"FAIL")

if __name__=="__main__":unittest.main()
