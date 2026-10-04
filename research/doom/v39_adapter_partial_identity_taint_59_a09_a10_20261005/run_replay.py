import ast,copy,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent; D=H.parent; A08=D/"v39_adapter_nested_identity_taint_59_a08_20261005"; FIX=D/"map01_v39_perkey_bridge_a01/results/construction-a01/candidate-events.jsonl"; SRC=D/"map01_overlap_controller_v39.py"; TEST=D/"test_map01_v39_typed_state_feedback.py"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):
 t=ast.parse(p.read_text(encoding="utf-8"));n=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=="input_edge_receipts");e={"hashlib":hashlib};exec(compile(ast.fix_missing_locations(ast.Module(body=[n],type_ignores=[])),str(p),"exec"),e);return e["input_edge_receipts"]
def summ(fn,rows):
 out=fn(copy.deepcopy(rows)); a=[x for x in out if x.get("status","").startswith("adapter_edge_")];p=[x for x in a if x.get("status")=="adapter_edge_brackets_paired"];return {"statuses":[x.get("status") for x in out],"adapter_receipts":len(a),"paired_timing_count":sum(x.get("down_edge_interval_ns") is not None and x.get("up_edge_interval_ns") is not None for x in p),"all_incomplete":len(a)>=2 and all(x.get("status")=="adapter_edge_receipt_incomplete" for x in a),"all_intervals_null":len(a)>=2 and all(x.get("down_edge_interval_ns") is None and x.get("up_edge_interval_ns") is None for x in a)}
def make_case(down,up,outer,nested,value):
 d=copy.deepcopy(down);d[outer[0]]=outer[1];d["physical_key_measurement"]["adapter_edge"][nested]=value;return [copy.deepcopy(down),d,copy.deepcopy(up)]
f9=json.loads((H/"A09_FREEZE.json").read_text(encoding="utf-8-sig"));f10=json.loads((H/"A10_FREEZE.json").read_text(encoding="utf-8-sig"));assert sha(H/"A09_PRE_FIX_COMPOSED_SOURCE.py")==f9["composed_source_sha256"];assert sha(A08/"BASELINE_SOURCE.py")==f9["frozen_a08_baseline_sha256"];assert sha(H/"A10_PRETEST_SOURCE.py")==f10["a09_source_sha256"];assert sha(H/"A10_PRETEST_TEST.py")==f10["a09_test_sha256"];assert sha(FIX)==f9["fixture_sha256"]==f10["fixture_sha256"]
events=[json.loads(x) for x in FIX.read_text(encoding="utf-8").splitlines() if x];down=next(x for x in events if x.get("event")=="input_admission");up=next(x for x in events if x.get("event")=="input_release_measurement");base=load(A08/"BASELINE_SOURCE.py");old9=load(H/"A09_PRE_FIX_COMPOSED_SOURCE.py");old10=load(H/"A10_PRETEST_SOURCE.py");new=load(SRC); a9=[];a10=[]
for outer in (("id","copied-program"),("step",99)):
 for nested in ("owner_id","actuation_id"):
  for value in (None,["malformed"]):
   rows=make_case(down,up,outer,nested,value);a9.append({"outer":outer,"nested":nested,"value":value,"baseline":summ(base,rows),"pre_fix":summ(old9,rows),"repaired":summ(new,rows)})
 for nested in ("key","intent_token"):
  for value in (None,["malformed"]):
   rows=make_case(down,up,outer,nested,value);a10.append({"outer":outer,"nested":nested,"value":value,"pre_fix":summ(old10,rows),"repaired":summ(new,rows)})
r={"candidate_source_sha256":sha(SRC),"candidate_test_sha256":sha(TEST),"fixture_sha256":sha(FIX),"A09":{"cases":a9,"baseline_false_pairs":sum(x["baseline"]["paired_timing_count"]>0 for x in a9),"pre_fix_false_pairs":sum(x["pre_fix"]["paired_timing_count"]>0 for x in a9),"repaired_false_pairs":sum(x["repaired"]["paired_timing_count"]>0 for x in a9)},"A10":{"cases":a10,"pre_fix_false_pairs":sum(x["pre_fix"]["paired_timing_count"]>0 for x in a10),"repaired_false_pairs":sum(x["repaired"]["paired_timing_count"]>0 for x in a10)}};(H/"REPLAY_RESULT.json").write_text(json.dumps(r,indent=2)+"\n");print(json.dumps({"source":r["candidate_source_sha256"],"test":r["candidate_test_sha256"],"A09":{k:v for k,v in r["A09"].items() if k!="cases"},"A10":{k:v for k,v in r["A10"].items() if k!="cases"}},indent=2))
