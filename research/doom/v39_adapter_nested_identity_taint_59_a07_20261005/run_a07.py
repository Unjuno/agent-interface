from __future__ import annotations
import ast, contextlib, hashlib, io, json, unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path("/src"); DOOM=ROOT/"research/doom"; HERE=DOOM/"v39_adapter_nested_identity_taint_59_a07_20261005"
BASE=HERE/"BASELINE_SOURCE.py"; SRC=DOOM/"map01_overlap_controller_v39.py"; TESTS=DOOM/"test_map01_v39_typed_state_feedback.py"; FIXTURE=DOOM/"map01_v39_perkey_bridge_a01/results/construction-a01/candidate-events.jsonl"; OUT=Path("/out/A07_RESULT.json")
FREEZE=json.loads((HERE/"A07_FREEZE.json").read_text(encoding="utf-8"))
METHODS=("test_input_edge_receipt_rejects_duplicate_adapter_rows","test_input_edge_receipt_rejects_unknown_outer_event_with_adapter_edge","test_input_edge_receipt_rejects_legacy_transition_with_adapter_edge","test_input_edge_receipt_rejects_outer_nested_token_conflict","test_input_edge_receipt_rejects_outer_group_split_for_same_actuation")
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
for path,key in ((BASE,"baseline_source_sha256"),(SRC,"candidate_source_sha256"),(TESTS,"test_sha256"),(FIXTURE,"fixture_sha256")):
 assert digest(path)==FREEZE[key], f"frozen hash mismatch: {key}"
def load_fn(path):
 tree=ast.parse(path.read_text(encoding="utf-8")); fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="input_edge_receipts"); env={"hashlib":hashlib}; exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(path),"exec"),env); return env["input_edge_receipts"]
def run(methods, projector):
 tree=ast.parse(TESTS.read_text(encoding="utf-8")); cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=="V39TypedStateFeedbackTests"); nodes=[next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name==m) for m in methods]; wrapper=ast.ClassDef(name="A07Regressions",bases=[ast.Attribute(value=ast.Name(id="unittest",ctx=ast.Load()),attr="TestCase",ctx=ast.Load())],keywords=[],body=nodes,decorator_list=[]); mod=ast.Module(body=[ast.Import(names=[ast.alias(name="json")]),ast.Import(names=[ast.alias(name="unittest")]),wrapper],type_ignores=[]); env={"HERE":DOOM,"controller":SimpleNamespace(input_edge_receipts=projector)}; exec(compile(ast.fix_missing_locations(mod),str(TESTS),"exec"),env); suite=unittest.defaultTestLoader.loadTestsFromTestCase(env["A07Regressions"]); stream=io.StringIO(); result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite); return result.wasSuccessful(),stream.getvalue(),result.testsRun,len(result.failures)+len(result.errors)
baseline=load_fn(BASE); candidate=load_fn(SRC); okb,logb,nb,fb=run(METHODS,baseline); okc,logc,nc,fc=run(METHODS,candidate)
# Explicit baseline characterization: each outer-id/step split leaves original pair falsely complete.
events=[json.loads(x) for x in FIXTURE.read_text(encoding="utf-8").splitlines()]; down=next(x for x in events if x.get("event")=="input_admission"); up=next(x for x in events if x.get("event")=="input_release_measurement"); cases=[]
for edge,row in (("down",down),("up",up)):
 for field,value in (("id","copied-program"),("step",99)):
  mutated=json.loads(json.dumps(row)); mutated[field]=value; rows=events+[mutated]; receipts=[x for x in baseline(rows) if x.get("status","").startswith("adapter_edge_")]; paired=sum(x.get("status")=="adapter_edge_brackets_paired" for x in receipts); cases.append({"case":f"duplicate_{edge}_{field}_changed","baseline_paired_receipts":paired,"baseline_false_pair":paired>=1})
for path in (SRC,TESTS): compile(path.read_text(encoding="utf-8"),str(path),"exec")
record={"experiment":"V39_ADAPTER_CROSS_GROUP_ACTUATION_TAINT_A07","baseline_head":FREEZE["baseline_head"],"baseline_source_sha256":digest(BASE),"candidate_source_sha256":digest(SRC),"test_sha256":digest(TESTS),"fixture_sha256":digest(FIXTURE),"baseline":{"passed":okb,"tests":nb,"failed_tests":fb,"output":logb},"candidate":{"passed":okc,"tests":nc,"failed_tests":fc,"output":logc},"baseline_mutation_cases":cases,"all_four_baseline_false_pairs":all(x["baseline_false_pair"] for x in cases),"syntax_compile":"PASS"}
OUT.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8"); print(json.dumps({k:v for k,v in record.items() if k not in ("baseline","candidate")},indent=2)); print("BASELINE\n"+logb+"CANDIDATE\n"+logc); raise SystemExit(0 if (record["all_four_baseline_false_pairs"] and okc and not okb) else 1)
