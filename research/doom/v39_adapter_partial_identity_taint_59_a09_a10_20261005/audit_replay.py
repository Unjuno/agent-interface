import ast,copy,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;D=H.parent;FIX=D/"map01_v39_perkey_bridge_a01/results/construction-a01/candidate-events.jsonl";SRC=D/"map01_overlap_controller_v39.py";TEST=H/"A11_TEST_PRE_ADDITION.py";R=json.loads((H/"REPLAY_RESULT.json").read_text());errors=[];checks=0
def ck(v,m):
 global checks
 checks+=1
 if not v:errors.append(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
t=ast.parse(SRC.read_text(encoding="utf-8"));n=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=="input_edge_receipts");e={"hashlib":hashlib};exec(compile(ast.fix_missing_locations(ast.Module(body=[n],type_ignores=[])),str(SRC),"exec"),e);project=e["input_edge_receipts"]
ck(sha(SRC)==R["candidate_source_sha256"],"source hash");ck(sha(TEST)==R["candidate_test_sha256"],"A09/A10 pre-A11 test snapshot hash");ck(sha(FIX)==R["fixture_sha256"],"fixture hash");ck(R["A09"]["baseline_false_pairs"]==8 and R["A09"]["pre_fix_false_pairs"]==8,"A09 red controls");ck(R["A09"]["repaired_false_pairs"]==0,"A09 repaired count");ck(R["A10"]["pre_fix_false_pairs"]==8 and R["A10"]["repaired_false_pairs"]==0,"A10 counts")
rows=[json.loads(x) for x in FIX.read_text(encoding="utf-8").splitlines() if x];down=next(x for x in rows if x.get("event")=="input_admission");up=next(x for x in rows if x.get("event")=="input_release_measurement")
for suite,fields in (("A09",("owner_id","actuation_id")),("A10",("key","intent_token"))):
 for c in R[suite]["cases"]:
  d=copy.deepcopy(down);d[c["outer"][0]]=c["outer"][1];d["physical_key_measurement"]["adapter_edge"][c["nested"]]=c["value"];out=project([copy.deepcopy(down),d,copy.deepcopy(up)]);a=[x for x in out if x.get("status","").startswith("adapter_edge_")];p=[x for x in a if x.get("status")=="adapter_edge_brackets_paired"];label=f"{suite}:{c['outer'][0]}:{c['nested']}:{c['value']}";ck(not p,"no paired receipt "+label);ck(len(a)>=2 and all(x.get("status")=="adapter_edge_receipt_incomplete" for x in a),"incomplete groups "+label);ck(len(a)>=2 and all(x.get("down_edge_interval_ns") is None and x.get("up_edge_interval_ns") is None for x in a),"null intervals "+label)
report={"audit":"PASS" if not errors else "FAIL","checks":checks,"errors":errors,"candidate_source_sha256":sha(SRC),"candidate_test_sha256":sha(TEST),"fixture_sha256":sha(FIX),"recomputed_mutations":16,"scope":"independent source AST/raw fixture replay; test binding uses A11_TEST_PRE_ADDITION.py because this replay freezes before A11"};(H/"REPLAY_AUDIT.json").write_text(json.dumps(report,indent=2)+"\n");print(json.dumps(report,indent=2));raise SystemExit(bool(errors))
