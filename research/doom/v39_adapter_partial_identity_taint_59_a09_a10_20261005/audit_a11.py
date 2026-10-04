import ast,copy,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;D=H.parent;O=H/"A11_RESULT.json";F=json.loads((H/"A11_FREEZE.json").read_text(encoding="utf-8-sig"));R=json.loads(O.read_text());SRC=D/"map01_overlap_controller_v39.py";TEST_SNAPSHOT=H/"A11_TEST_PRE_ADDITION.py";FIX=D/"map01_v39_perkey_bridge_a01/results/construction-a01/candidate-events.jsonl";BASE=D/"v39_adapter_nested_identity_taint_59_a08_20261005/BASELINE_SOURCE.py";errors=[];checks=0
def ck(v,m):
 global checks
 checks+=1
 if not v:errors.append(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):
 t=ast.parse(p.read_text(encoding="utf-8"));n=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=="input_edge_receipts");e={"hashlib":hashlib};exec(compile(ast.fix_missing_locations(ast.Module(body=[n],type_ignores=[])),str(p),"exec"),e);return e["input_edge_receipts"]
ck(sha(H/"A11_FREEZE.json")==R["freeze_sha256"],"corrected freeze hash");ck(sha(SRC)==F["candidate_source_sha256"]==R["source_sha256"],"candidate source pin");ck(sha(TEST_SNAPSHOT)==F["candidate_test_sha256"]==R["test_sha256"],"pre-addition test snapshot pin");ck(sha(BASE)==F["baseline_source_sha256"],"baseline source pin");ck(sha(FIX)==F["fixture_sha256"]==R["fixture_sha256"],"fixture pin")
fixture=[json.loads(x) for x in FIX.read_text(encoding="utf-8").splitlines() if x];down=next(x for x in fixture if x.get("event")=="input_admission");up=next(x for x in fixture if x.get("event")=="input_release_measurement");old,new=load(BASE),load(SRC)
for case in R["cases"]:
 d=copy.deepcopy(down);d[case["outer_field"]]=case["value"];rows=[copy.deepcopy(down),d,copy.deepcopy(up)];label=repr((case["outer_field"],case["value"]))
 for name,fn in (("baseline",old),("candidate",new)):
  receipts=fn(copy.deepcopy(rows));adapters=[x for x in receipts if x.get("status","").startswith("adapter_edge_")];paired=[x for x in adapters if x.get("status")=="adapter_edge_brackets_paired"];unavailable=any(x.get("status")=="identity_unavailable" for x in receipts)
  if name=="baseline":ck(bool(paired) and any(x.get("down_edge_interval_ns") is not None and x.get("up_edge_interval_ns") is not None for x in paired),"baseline false-pair control "+label)
  else:ck(unavailable and len(adapters)==1 and adapters[0].get("status")=="adapter_edge_receipt_incomplete" and adapters[0].get("down_edge_interval_ns") is None and adapters[0].get("up_edge_interval_ns") is None,"candidate fail-closed "+label)
report={"audit":"PASS" if not errors else "FAIL","checks":checks,"errors":errors,"replayed_cases":len(R["cases"]),"source_sha256":sha(SRC),"test_snapshot_sha256":sha(TEST_SNAPSHOT),"fixture_sha256":sha(FIX),"scope":"independent raw fixture replay of A11's four malformed outer identity cases"};(H/"A11_AUDIT.json").write_text(json.dumps(report,indent=2)+"\n");print(json.dumps(report,indent=2));raise SystemExit(bool(errors))
