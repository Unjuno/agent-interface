"""Raw/source-derived independent check of the A05 saved replay."""
import hashlib,json
from pathlib import Path
ROOT=Path("/src"); DOOM=ROOT/"research/doom"; HERE=DOOM/"v39_adapter_event_type_boundary_59_a05_20261005"; RAW=DOOM/"map01_v39_perkey_bridge_a01/results/construction-a01/candidate-events.jsonl"
record=json.loads((Path("/evidence")/"A05_RESULT.json").read_text(encoding="utf-8")); freeze=json.loads((HERE/"A05_FREEZE.json").read_text(encoding="utf-8")); fixture=[json.loads(x) for x in RAW.read_text(encoding="utf-8").splitlines() if x]; errors=[]; checks=0
def check(value,msg):
 global checks
 checks+=1
 if not value: errors.append(msg)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
check(record.get("experiment")==freeze.get("experiment"),"experiment identity"); check(record.get("baseline_commit")==freeze["baseline"]["commit"],"baseline commit"); check(record.get("baseline_source_sha256")==sha(HERE/"BASELINE_SOURCE.py")==freeze["baseline"]["source_sha256"],"frozen baseline source"); check(record.get("candidate_source_sha256")==sha(DOOM/"map01_overlap_controller_v39.py"),"candidate source hash"); check(record.get("test_sha256")==sha(DOOM/"test_map01_v39_typed_state_feedback.py"),"test source hash"); check(record.get("fixture_sha256")==sha(RAW)==freeze["baseline"]["fixture_sha256"],"raw fixture hash")
check(record.get("baseline",{}).get("expected_fail") is True and record.get("baseline",{}).get("tests")==3,"baseline expected failures"); check(record.get("candidate",{}).get("passed") is True and record.get("candidate",{}).get("tests")==3 and record["candidate"].get("failed_tests")==0,"candidate pass")
expected=["duplicate_down_unknown_kind","duplicate_up_unknown_kind","down_unknown_kind","up_unknown_kind","duplicate_up_as_legacy_transition","only_legacy_transition_up"]; check(record.get("subcases")==expected,"frozen mutation list")
down=next((r for r in fixture if r.get("event")=="input_admission"),None); up=next((r for r in fixture if r.get("event")=="input_release_measurement"),None); check(type(down) is dict and type(up) is dict,"fixture edges")
if type(down) is dict and type(up) is dict:
 identity=("id","step","key","intent_token"); check(tuple(down.get(k) for k in identity)==tuple(up.get(k) for k in identity),"raw edge identity"); check(down.get("physical_key_measurement",{}).get("adapter_edge",{}).get("edge")=="down","raw DOWN discriminator"); check(up.get("physical_key_measurement",{}).get("adapter_edge",{}).get("edge")=="up","raw UP discriminator")
b=record.get("baseline",{}).get("output",""); c=record.get("candidate",{}).get("output",""); check(all(case in b for case in ("duplicate_down_unknown_kind","duplicate_up_unknown_kind","duplicate_up_as_legacy_transition")),"baseline red cases"); check(b.count("adapter_edge_brackets_paired")>=3,"baseline false pairs visible"); check(c.count(" ... ok")==3 and c.rstrip().endswith("OK"),"candidate green output")
report={"audit":"PASS" if not errors else "FAIL","checks":checks,"errors":errors,"scope":"one retained synthetic X-adapter fixture; exact source projection only"}; (Path("/audit")/"A05_AUDIT.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); print(json.dumps(report,indent=2)); raise SystemExit(bool(errors))
