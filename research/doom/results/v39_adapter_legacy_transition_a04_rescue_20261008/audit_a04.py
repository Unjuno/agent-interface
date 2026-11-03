"""Independently audit A04 replay hashes, fixture identity, and red/green output."""
import hashlib
import json
from pathlib import Path
ROOT=Path("/src")
DOOM=ROOT/"research/doom"
HERE=DOOM/"results/v39_adapter_edge_cardinality_59_a01_20261005/a04-legacy-transition-outer-event"
RAW=DOOM/"map01_v39_perkey_bridge_a01/results/construction-a01/candidate-events.jsonl"
record=json.loads((Path("/evidence")/"A04_RESULT.json").read_text(encoding="utf-8"))
fixture=[json.loads(line) for line in RAW.read_text(encoding="utf-8").splitlines() if line]
errors=[]; checks=0
def check(value,message):
 global checks
 checks+=1
 if not value: errors.append(message)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
check(record.get("experiment")=="V39_LEGACY_TRANSITION_A04","experiment identity")
check(record.get("baseline_commit")=="46bed14701c6ba7d509c620bf6f582c84993f949","baseline commit")
check(record.get("baseline_source_sha256")==sha(HERE/"BASELINE_SOURCE.py"),"baseline source hash")
check(record.get("candidate_source_sha256")==sha(DOOM/"map01_overlap_controller_v39.py"),"candidate source hash")
check(record.get("test_sha256")==sha(DOOM/"test_map01_v39_typed_state_feedback.py"),"test source hash")
check(record.get("fixture_sha256")==sha(RAW),"raw fixture hash")
check(record.get("baseline",{}).get("expected_fail") is True and record.get("baseline",{}).get("tests")==2,"baseline expected failure")
check(record.get("candidate",{}).get("passed") is True and record.get("candidate",{}).get("tests")==2,"candidate passes two tests")
check(record.get("subcases")==["duplicate_up_as_legacy_transition","only_legacy_transition_up"],"mutation set")
down=next((row for row in fixture if row.get("event")=="input_admission"),None)
up=next((row for row in fixture if row.get("event")=="input_release_measurement"),None)
check(type(down) is dict and type(up) is dict,"raw fixture edges")
if type(down) is dict and type(up) is dict:
 keys=("id","step","key","intent_token")
 check(tuple(down.get(k) for k in keys)==tuple(up.get(k) for k in keys),"raw pair identity")
 check(up.get("physical_key_measurement",{}).get("adapter_edge",{}).get("edge")=="up","raw UP discriminator")
b=record.get("baseline",{}).get("output",""); c=record.get("candidate",{}).get("output","")
check("duplicate_up_as_legacy_transition" in b and "adapter_edge_brackets_paired" in b,"baseline exposes paired duplicate")
check(c.count(" ... ok")==2 and c.rstrip().endswith("OK"),"candidate green output")
report={"audit":"PASS" if not errors else "FAIL","checks":checks,"errors":errors,"scope":"one retained synthetic X-adapter fixture; deterministic projector only"}
(Path("/audit")/"A04_AUDIT.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,indent=2))
raise SystemExit(bool(errors))
