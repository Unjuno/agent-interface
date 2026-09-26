import hashlib
import json
import os
import tempfile
import unittest

import torch
os.environ.setdefault("NEEDLE_SEED","3792")
os.environ.setdefault("NEEDLE_OUTPUT","/tmp/needle-construct")
import runner
import loader
import audit


SEEDS=(100000,100100,100200,100300,100400,100500,100600,100700,100800,100900)


def zero_state(role):
    if role=="A":
        return {"enc.0.weight":[[0.0]*8 for _ in range(16)],"enc.0.bias":[0.0]*16,
                "head.weight":[[0.0]*16 for _ in range(4)],"head.bias":[0.0]*4}
    return {"core.enc.0.weight":[[0.0]*8 for _ in range(16)],"core.enc.0.bias":[0.0]*16,
            "core.head.weight":[[0.0]*16 for _ in range(4)],"core.head.bias":[0.0]*4,
            "a":[[0.0]*2 for _ in range(16)],"b":[[0.0]*4 for _ in range(2)]}


class RobustnessConstructionTests(unittest.TestCase):
    def test_fresh_seed_schedule_and_component_rng_offsets_are_disjoint(self):
        self.assertEqual(runner.SEED,3792)
        self.assertEqual(SEEDS,(100000,100100,100200,100300,100400,100500,100600,100700,100800,100900))
        self.assertEqual(len(set(SEEDS)),10)
        self.assertFalse(set(SEEDS)&{3788,3789,3790,3781,3782,3783,3787,3791})
        used={s+o for s in SEEDS for o in (*range(1,7),10,11,12)}
        self.assertEqual(len(used),90)
        prior=(3781,3782,3783,3787,3788,3789,3790,3791)
        prior_stream={s+o for s in prior for o in (*range(1,7),10,11,12)}
        self.assertFalse(used&prior_stream)

    def test_synthetic_data_and_labels_are_seeded(self):
        a=runner.data(32,9001); b=runner.data(32,9001)
        self.assertTrue(torch.equal(a,b))
        self.assertEqual(runner.labels(a,"A").shape,(32,))
        self.assertEqual(runner.labels(a,"B").shape,(32,))
        self.assertEqual(runner.labels(a,"C").shape,(32,))
        self.assertFalse(torch.equal(runner.labels(a,"A"),runner.labels(a,"B")))
        self.assertFalse(torch.equal(runner.labels(a,"A"),runner.labels(a,"C")))

    def test_architecture_and_tensor_shapes_without_training(self):
        core=runner.Core()
        self.assertEqual(tuple(core.enc[0].weight.shape),(16,8))
        self.assertEqual(tuple(core.head.weight.shape),(4,16))
        adapter=runner.LoRA(core)
        self.assertEqual(tuple(adapter.a.shape),(16,2))
        self.assertEqual(tuple(adapter.b.shape),(2,4))
        self.assertEqual(runner.BASE_STEPS,400)
        self.assertEqual(runner.ADAPTER_STEPS,120)
        self.assertEqual(runner.BASE_STEPS+2*runner.ADAPTER_STEPS,640)

    def test_data_only_package_validates_from_a_fresh_mapping(self):
        seed=3792
        artifact={"schema":"unjuno.role-skill.numeric-json.v1","generation":seed,
          "architecture":{"input":8,"hidden":16,"classes":4,"rank":2,"roles":["A","B","C"]},
          "graph":{"nodes":[{"id":r,"version":r+"-v1"} for r in ("A","B","C")],"edges":[["A","B"],["B","C"]],"scope":"synthetic-fixture-v1"},
          "provenance":{"allocation":"needle-role-skill-robustness-3890-v1","predecessor_issue":3890,"seed":seed,"family":"synthetic-role-adapter-v1"},
          "tensors":{r:zero_state(r) for r in ("A","B","C")}}
        artifact["payload_sha256"]=loader.hashlib.sha256(loader.canonical(artifact)).hexdigest()
        expected={"seed":seed,"roles":{}}
        with tempfile.TemporaryDirectory() as td:
            path=td+"/skill.json"
            with open(path,"w",encoding="utf-8") as f: json.dump(artifact,f)
            obj,sha=loader.validate(path,expected)
            self.assertEqual(obj["generation"],seed)
            self.assertEqual(len(sha),64)

    def test_loader_controls_are_fail_closed_and_graph_receipts_are_generation_bound(self):
        seed=3792; artifact={"tensors":{r:zero_state(r) for r in ("A","B","C")}}
        run=loader.exercise(artifact,{"seed":seed},seed)
        self.assertEqual(run["flow"],["ADVANCE","ADVANCE"])
        self.assertEqual(run["cursor"],"C")
        self.assertEqual(run["old_receipt"],"YIELD")
        self.assertEqual(run["fixture_emissions"],2)
        self.assertEqual(run["controls"]["duplicate_receipt_second"],"YIELD")
        self.assertEqual(run["controls"]["wrong_scope"],"YIELD")
        self.assertEqual(run["controls"]["truncated"],"YIELD")
        self.assertEqual(run["controls"]["tampered_digest"],"YIELD")

    def test_independent_audit_forward_is_deterministic_and_role_shaped(self):
        state=zero_state("A"); x=torch.randn(8,8,generator=torch.Generator().manual_seed(22)).tolist()
        a=audit.independent_predictions("A",state,x); b=audit.independent_predictions("A",state,x)
        self.assertEqual(a,b)
        self.assertEqual(len(a),8)
        self.assertEqual(set(a),{0})

    def test_issue_and_allocation_identity_are_fixed(self):
        self.assertEqual(audit.ALLOCATION,"needle-role-skill-robustness-3890-v1")
        self.assertEqual(audit.SEEDS,SEEDS)
        with open("ISSUE_CONTRACT.md",encoding="utf-8") as f:
            self.assertIn("100000, 100100",f.read())

    def test_construction_does_not_train(self):
        from unittest.mock import patch
        with patch.object(runner,"train",side_effect=AssertionError("training forbidden during construction")):
            x=runner.data(4,10)
            self.assertEqual(tuple(x.shape),(4,8))
            self.assertEqual(len(loader.Graph(3792).state()),4)


if __name__=="__main__": unittest.main(verbosity=2)
