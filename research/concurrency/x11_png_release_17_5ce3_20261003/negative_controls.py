"""Corrupt only in-memory copies of saved rows; never invoke scientific input."""
import copy
import hashlib
import json
from pathlib import Path
from auditor import audit

ROOT=Path(__file__).resolve().parent
raw=ROOT/"runs/candidate/evidence/raw.jsonl"
before=hashlib.sha256(raw.read_bytes()).hexdigest()
original=[json.loads(line) for line in raw.read_text().splitlines()]
plan=json.loads((ROOT/"PLAN.json").read_text())
mutations={
    "duplicate_cell": lambda rows: rows.__setitem__(1,copy.deepcopy(rows[0])),
    "wrong_policy": lambda rows: rows[0].__setitem__("policy","separate"),
    "checkpoint_label": lambda rows: rows[3]["checkpoint"].__setitem__("down",True),
    "terminal_button": lambda rows: rows[0]["terminal"].__setitem__("buttons",256),
    "false_release": lambda rows: rows[0]["program"]["execution"]["releases"][0].__setitem__("verified",False),
    "late_press": lambda rows: rows[0]["app_events"].append({"kind":"press","at_ns":10**20,"keycode":rows[0]["keycode"]}),
    "short_fault": lambda rows: rows[2]["times"].__setitem__("write_resume",rows[2]["times"]["cancel_request"]+1),
    "wrong_program": lambda rows: rows[0]["program_input"]["ops"][1].__setitem__("key","F9"),
    "wrong_raw_capture": lambda rows: rows[0]["source_capture"].__setitem__("sha256","c"*64),
    "wrong_png_payload": lambda rows: rows[0]["png_write_payload"].__setitem__("sha256","c"*64),
    "false_cleanup": lambda rows: rows[1]["cleanup_response"].__setitem__("verified",False),
    "missing_physical_up": lambda rows: [s.__setitem__("keymap",rows[0]["samples"][0]["keymap"]) for s in rows[0]["samples"]],
}
result=[]
for name,mutate in mutations.items():
    rows=copy.deepcopy(original); mutate(rows)
    try:
        outcome=audit(rows,plan)["status"]
        if outcome.startswith("PASS"): raise AssertionError("corruption accepted: "+name)
        result.append({"mutation":name,"outcome":outcome})
    except ValueError as error: result.append({"mutation":name,"outcome":"REJECT","detail":str(error)})
assert hashlib.sha256(raw.read_bytes()).hexdigest() == before
record={"n":len(result),"rejected_or_nonpass":len(result),"raw_sha256":before,
        "scientific_invocations":0,"mutations":result}
with (ROOT/"validation/negative_controls.json").open("x") as stream: json.dump(record,stream,indent=2); stream.write("\n")
print(json.dumps(record))
