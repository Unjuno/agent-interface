"""Post-run copied-packet audit qualification; no original mutation or codec run."""
import copy,hashlib,json
from pathlib import Path
from auditor import validate_packet,canonical
ROOT=Path(__file__).parent
records=json.loads((ROOT/"INPUT.json").read_text())["records"];by_id={r["case_id"]:r for r in records}
raw=(ROOT/"runs/candidate/evidence/packets.jsonl").read_bytes();rows=[json.loads(s)for s in raw.splitlines()]
source=next(r for r in rows if r["family"]=="native"and r["policy"]=="CONSERVATIVE_PROFILE")
def coherent(r):
    b=canonical(r["packet"]);r.update(bytes=len(b),wire_hex=b.hex())
mutations={
"decision_flip":lambda r:r["decision"].__setitem__("owned_up",not r["decision"]["owned_up"]),
"missing_residual":lambda r:r["packet"]["payload"].pop("o"),
"byte_count":lambda r:r.__setitem__("bytes",0),
"wire_substitution":lambda r:r.__setitem__("wire_hex","00"),
"source_meta":lambda r:r["packet"]["meta"].__setitem__("nonce","foreign"),
"residual_flip":lambda r:r["packet"]["payload"].__setitem__("o",not r["packet"]["payload"]["o"]),
"bool_as_int":lambda r:r["packet"]["payload"].__setitem__("v",int(r["packet"]["payload"]["v"])),
"decision_bool_as_int":lambda r:r["decision"].__setitem__("owned_up",int(r["decision"]["owned_up"])),
}
checks=[]
for name,mutate in mutations.items():
    row=copy.deepcopy(source);mutate(row)
    if name not in("byte_count","wire_substitution"):coherent(row)
    try:validate_packet(row,by_id[row["case_id"]]);accepted=True
    except (ValueError,KeyError,TypeError):accepted=False
    checks.append({"name":name,"frozen_auditor_accepted":accepted})
result={"status":"POSTRUN_AUDITOR_TYPE_QUALIFICATION","checks":checks,"false_accepts":sum(c["frozen_auditor_accepted"]for c in checks),"original_packets_sha256":hashlib.sha256(raw).hexdigest(),"original_unchanged":hashlib.sha256((ROOT/"runs/candidate/evidence/packets.jsonl").read_bytes()).hexdigest()==hashlib.sha256(raw).hexdigest(),"native_inputs":0,"formal_auditor_invocations":0}
(ROOT/"validation").mkdir(exist_ok=True)
with(ROOT/"validation/copied_controls_first.json").open("x")as f:json.dump(result,f,indent=2);f.write("\n")
print(json.dumps(result))
