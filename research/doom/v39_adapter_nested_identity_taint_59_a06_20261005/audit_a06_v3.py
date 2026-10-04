"""Independent raw-derived replay audit for outer/nested token contradictions."""
import ast,copy,hashlib,json
from pathlib import Path
ROOT=Path("/src"); DOOM=ROOT/"research/doom"; HERE=DOOM/"v39_adapter_nested_identity_taint_59_a06_20261005"; RAW=DOOM/"map01_v39_perkey_bridge_a01/results/construction-a01/candidate-events.jsonl"
record=json.loads((Path("/evidence")/"A06_RESULT.json").read_text(encoding="utf-8")); freeze=json.loads((HERE/"A06_FREEZE.json").read_text(encoding="utf-8")); fixture=[json.loads(x) for x in RAW.read_text(encoding="utf-8").splitlines() if x]; errors=[]; checks=0
def ck(value,msg):
 global checks
 checks+=1
 if not value: errors.append(msg)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load_projector(path):
 tree=ast.parse(path.read_text(encoding="utf-8")); node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="input_edge_receipts"); module=ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])); env={"hashlib":hashlib}; exec(compile(module,str(path),"exec"),env); return env["input_edge_receipts"]
ck(record.get("experiment")==freeze.get("experiment"),"experiment identity"); ck(record.get("baseline_commit")==freeze["baseline"]["commit"],"baseline commit"); ck(record.get("baseline_source_sha256")==sha(HERE/"BASELINE_SOURCE.py")==freeze["baseline"]["source_sha256"],"frozen baseline source"); ck(record.get("candidate_source_sha256")==sha(DOOM/"map01_overlap_controller_v39.py"),"candidate source hash"); ck(record.get("test_sha256")==sha(DOOM/"test_map01_v39_typed_state_feedback.py"),"test source hash"); ck(record.get("fixture_sha256")==sha(RAW)==freeze["baseline"]["fixture_sha256"],"raw fixture hash")
ck(record.get("baseline",{}).get("expected_fail") is True and record.get("baseline",{}).get("tests")==4 and record["baseline"].get("failed_tests")==2,"baseline two conflict failures"); ck(record.get("candidate",{}).get("passed") is True and record.get("candidate",{}).get("tests")==4 and record["candidate"].get("failed_tests")==0,"candidate four-test pass")
expected=["duplicate_down_identical","duplicate_up_identical","duplicate_both_identical","duplicate_down_conflicting","duplicate_up_conflicting","duplicate_down_unknown_kind","duplicate_up_unknown_kind","down_unknown_kind","up_unknown_kind","duplicate_up_as_legacy_transition","only_legacy_transition_up","duplicate_down_outer_token_changed","duplicate_up_outer_token_changed"]; ck(record.get("subcases")==expected,"frozen treatment list")
down=next((r for r in fixture if r.get("event")=="input_admission"),None); up=next((r for r in fixture if r.get("event")=="input_release_measurement"),None); ck(type(down) is dict and type(up) is dict,"raw edge rows")
if type(down) is dict and type(up) is dict:
 keys=("id","step","key","intent_token"); ck(tuple(down.get(k) for k in keys)==tuple(up.get(k) for k in keys),"fixture outer identity"); ck(down.get("physical_key_measurement",{}).get("adapter_edge",{}).get("edge")=="down","fixture nested DOWN"); ck(up.get("physical_key_measurement",{}).get("adapter_edge",{}).get("edge")=="up","fixture nested UP")
baseline=load_projector(HERE/"BASELINE_SOURCE.py"); candidate=load_projector(DOOM/"map01_overlap_controller_v39.py")
for edge,row,rows in (("down",down,[down,up]),("up",up,[down,up])):
 duplicate=copy.deepcopy(row); duplicate["intent_token"]="contradictory-outer-token"; mutated=copy.deepcopy(rows); mutated.insert(1,duplicate) if edge=="down" else mutated.append(duplicate)
 base_receipts=baseline(mutated); base_adapter=[r for r in base_receipts if r.get("status","").startswith("adapter_edge_")]; base_pairs=[r for r in base_adapter if r.get("status")=="adapter_edge_brackets_paired"]
 ck(len(base_pairs)==1 and base_pairs[0].get("down_edge_interval_ns") is not None and base_pairs[0].get("up_edge_interval_ns") is not None,"baseline exposes original paired timing for "+edge+" conflict")
 cand_receipts=candidate(mutated); cand_adapter=[r for r in cand_receipts if r.get("status","").startswith("adapter_edge_")]
 ck(bool(cand_adapter) and all(r.get("status")=="adapter_edge_receipt_incomplete" and r.get("down_edge_interval_ns") is None and r.get("up_edge_interval_ns") is None for r in cand_adapter),"candidate taints both groups for "+edge+" conflict")
b=record.get("baseline",{}).get("output",""); c=record.get("candidate",{}).get("output",""); ck(all(case in b for case in ("duplicate_down_outer_token_changed","duplicate_up_outer_token_changed")),"baseline red test names"); ck(c.count(" ... ok")==4 and c.rstrip().endswith("OK"),"candidate green output")
report={"audit":"PASS" if not errors else "FAIL","checks":checks,"errors":errors,"scope":"one retained synthetic X-adapter fixture; exact baseline/candidate projector replay"}; (Path("/audit")/"A06_AUDIT_V3.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); print(json.dumps(report,indent=2)); raise SystemExit(bool(errors))
