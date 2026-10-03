"""In-memory saved-data corruptions, not formal/native replay."""
import copy
import hashlib
import json
from pathlib import Path
from auditor import audit
ROOT=Path(__file__).resolve().parent
raw=ROOT/"runs/candidate/evidence/raw.jsonl"; before=hashlib.sha256(raw.read_bytes()).hexdigest()
rows=[json.loads(s) for s in raw.read_text().splitlines()]; plan=json.loads((ROOT/"PLAN.json").read_text())
mutations={
    "duplicate":lambda r:r.__setitem__(1,copy.deepcopy(r[0])),
    "observation_join":lambda r:r[0]["source_capture"].__setitem__("sha256","c"*64),
    "missing_cleanup":lambda r:r[2]["release_calls"].pop(0),
    "missing_program_release":lambda r:r[2]["release_calls"].pop(1),
    "query_bracket":lambda r:r[0]["samples"][0].__setitem__("query_started_ns",10**20),
    "unverified_release":lambda r:r[0]["release_calls"][0]["result"].__setitem__("verified",False),
    "short_fault":lambda r:r[2]["times"].__setitem__("write_resume",r[2]["times"]["cancel_request"]+1),
    "healthy_muted":lambda r:r[0]["app_events"].pop(1),
    "reference_emits":lambda r:r[3]["positive_input_calls"][1].__setitem__("native_called",True),
    "terminal_button":lambda r:r[0]["terminal"].__setitem__("buttons",256),
    "early_checkpoint":lambda r:r[2]["times"].__setitem__("checkpoint",r[2]["times"]["cancel_request"]+1),
    "false_completed_reference":lambda r:r[3]["program"].__setitem__("status","completed"),
    "owner_emissions":lambda r:r[2]["positive_input_calls"][1].__setitem__("emissions_before",7),
    "payload_substitute":lambda r:r[0]["png_write_payload"].__setitem__("sha256","c"*64),
}
records=[]
for name,mutate in mutations.items():
    case=copy.deepcopy(rows); mutate(case)
    try: audit(case,plan)
    except ValueError as error: records.append({"mutation":name,"rejected":True,"detail":str(error)})
    else: raise AssertionError("corruption not rejected: "+name)
assert hashlib.sha256(raw.read_bytes()).hexdigest()==before
result={"n":len(records),"rejected":len(records),"raw_sha256":before,"scientific_invocations":0,"mutations":records}
with (ROOT/"validation/negative_controls.json").open("x") as stream: json.dump(result,stream,indent=2);stream.write("\n")
print(json.dumps(result))
