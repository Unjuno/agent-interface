"""Copied-row adversarial projections; original evidence is never edited."""
import copy,hashlib,json
from pathlib import Path
from auditor import audit
ROOT=Path(__file__).parent
raw=(ROOT/"runs/candidate/evidence/raw.jsonl").read_bytes()
rows=[json.loads(s)for s in raw.splitlines()];plan=json.loads((ROOT/"PLAN.json").read_text())
base=next(i for i,r in enumerate(rows)if r["policy"]=="empty_scope"and r["context"]=="crash")
ref=next(i for i,r in enumerate(rows)if r["policy"]=="prearmed_scope"and r["context"]=="crash")
healthy=next(i for i,r in enumerate(rows)if r["context"]=="healthy")
mutations={
"duplicate_cell":lambda r:r.__setitem__(-1,copy.deepcopy(r[0])),
"owner_pid":lambda r:r[base]["capability"].__setitem__("owner_pid",999999),
"registration_late":lambda r:r[base]["supervisor"]["registered"].__setitem__("at_ns",r[base]["times"]["owner_ready"]+1),
"death_generation":lambda r:r[base]["supervisor"]["result"].__setitem__("death_start_ticks",999999),
"death_sample_live":lambda r:r[base]["supervisor"]["result"]["death_observations"]["samples"][-1].__setitem__("state","R"),
"truncated_keymap":lambda r:r[base]["samples"][0].__setitem__("keymap","00"),
"early_checkpoint":lambda r:next(s for s in r[base]["samples"]if s["tag"]=="checkpoint").__setitem__("query_started_ns",0),
"program_identity":lambda r:r[base]["owner"]["program_input"].__setitem__("program_id","foreign"),
"wrong_program_key":lambda r:r[base]["owner"]["program_input"]["ops"][1].__setitem__("key","F9"),
"missing_kill_exit":lambda r:r[base]["owner"].__setitem__("returncode",0),
"helper_emission_count":lambda r:r[ref]["supervisor"]["result"].__setitem__("emissions",0),
"wrong_helper_scope":lambda r:r[ref]["supervisor"]["result"].__setitem__("scope",{}),
"missing_app_up":lambda r:r[base]["app_events"].pop(),
"terminal_down":lambda r:next(s for s in r[base]["samples"]if s["tag"]=="terminal").__setitem__("keymap",next(s for s in r[base]["samples"]if s["tag"]=="held")["keymap"]),
"hidden_emergency":lambda r:r[base]["final_emergency"].__setitem__("emissions",1),
"short_normal_wait":lambda r:r[healthy]["owner"]["completed"]["execution"]["waits"][0].__setitem__("ended_ns",r[healthy]["times"]["owner_ready"]),
}
checks=[]
for name,mutate in mutations.items():
    projection=copy.deepcopy(rows);mutate(projection)
    try: value=audit(projection,plan)
    except (ValueError,KeyError,TypeError)as e: checks.append({"name":name,"rejected":True,"error":str(e)})
    else:raise AssertionError("invalid projection accepted: "+name+" "+str(value))
result={"saved_raw_sha256":hashlib.sha256(raw).hexdigest(),"original_unchanged":hashlib.sha256((ROOT/"runs/candidate/evidence/raw.jsonl").read_bytes()).hexdigest()==hashlib.sha256(raw).hexdigest(),"invalid_projections":len(checks),"checks":checks,"native_invocations":0,"formal_auditor_invocations":0,"scope":"audit function copied-row schema/death/scope/timing gates, not CLI actor-stream mutation or all alternative classifiers"}
with(ROOT/"validation/copied_controls.json").open("x")as f:json.dump(result,f,indent=2);f.write("\n")
print(json.dumps(result))
