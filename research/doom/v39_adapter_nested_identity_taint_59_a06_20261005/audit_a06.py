"""Independent raw/source-derived audit of the A06 saved replay."""
import hashlib,json
from pathlib import Path
ROOT=Path("/src"); DOOM=ROOT/"research/doom"; HERE=DOOM/"v39_adapter_nested_identity_taint_59_a06_20261005"; RAW=DOOM/"map01_v39_perkey_bridge_a01/results/construction-a01/candidate-events.jsonl"
record=json.loads((Path("/evidence")/"A06_RESULT.json").read_text(encoding="utf-8")); freeze=json.loads((HERE/"A06_FREEZE.json").read_text(encoding="utf-8")); fixture=[json.loads(x) for x in RAW.read_text(encoding="utf-8").splitlines() if x]; errors=[]; checks=0
def ck(value,msg):
 global checks
 checks+=1
 if not value: errors.append(msg)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
ck(record.get("experiment")==freeze.get("experiment"),"experiment identity"); ck(record.get("baseline_commit")==freeze["baseline"]["commit"],"baseline commit"); ck(record.get("baseline_source_sha256")==sha(HERE/"BASELINE_SOURCE.py")==freeze["baseline"]["source_sha256"],"frozen baseline hash"); ck(record.get("candidate_source_sha256")==sha(DOOM/"map01_overlap_controller_v39.py"),"candidate source hash"); ck(record.get("test_sha256")==sha(DOOM/"test_map01_v39_typed_state_feedback.py"),"test hash"); ck(record.get("fixture_sha256")==sha(RAW)==freeze["baseline"]["fixture_sha256"],"fixture hash")
ck(record.get("baseline",{}).get("expected_fail") is True and record.get("baseline",{}).get("tests")==4,"baseline expected fail"); ck(record.get("candidate",{}).get("passed") is True and record.get("candidate",{}).get("tests")==4 and record["candidate"].get("failed_tests")==0,"candidate pass")
expected=["duplicate_down_identical","duplicate_up_identical","duplicate_both_identical","duplicate_down_conflicting","duplicate_up_conflicting","duplicate_down_unknown_kind","duplicate_up_unknown_kind","down_unknown_kind","up_unknown_kind","duplicate_up_as_legacy_transition","only_legacy_transition_up","duplicate_down_outer_token_changed","duplicate_up_outer_token_changed"]; ck(record.get("subcases")==expected,"mutation list")
down=next((r for r in fixture if r.get("event")=="input_admission"),None); up=next((r for r in fixture if r.get("event")=="input_release_measurement"),None); ck(type(down) is dict and type(up) is dict,"raw fixture edge rows")
if type(down) is dict and type(up) is dict:
 keys=("id","step","key","intent_token"); ck(tuple(down.get(k) for k in keys)==tuple(up.get(k) for k in keys),"raw pair outer identity"); ck(down.get("physical_key_measurement",{}).get("adapter_edge",{}).get("edge")=="down","raw nested DOWN"); ck(up.get("physical_key_measurement",{}).get("adapter_edge",{}).get("edge")=="up","raw nested UP")
b=record.get("baseline",{}).get("output",""); c=record.get("candidate",{}).get("output",""); ck(all(case in b for case in ("duplicate_down_unknown_kind","duplicate_up_unknown_kind","duplicate_up_as_legacy_transition","duplicate_down_outer_token_changed","duplicate_up_outer_token_changed")),"baseline failure cases present"); ck(b.count("adapter_edge_brackets_paired")>=5,"baseline paired false positives visible"); ck(c.count(" ... ok")==4 and c.rstrip().endswith("OK"),"candidate green output")
report={"audit":"PASS" if not errors else "FAIL","checks":checks,"errors":errors,"scope":"one retained synthetic X-adapter fixture; deterministic projection only"}; (Path("/audit")/"A06_AUDIT.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); print(json.dumps(report,indent=2)); raise SystemExit(bool(errors))
