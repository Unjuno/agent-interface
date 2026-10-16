from __future__ import annotations
import copy, hashlib, importlib.util, json
from pathlib import Path

HERE=Path(__file__).resolve().parent
OLD=HERE/"audit_a04.py"
class AuditFailure(ValueError): pass
def need(ok,message):
    if not ok: raise AuditFailure(message)
def exact(a,b):
    if type(a) is not type(b): return False
    if type(a) is dict: return a.keys()==b.keys() and all(exact(a[k],b[k]) for k in a)
    if type(a) is list: return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    return a==b
def load_old():
    spec=importlib.util.spec_from_file_location("a04_original_frozen_audit",OLD)
    need(spec is not None and spec.loader is not None,"A04 auditor unavailable")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def verify_v2_freeze():
    raw=(HERE/"FREEZE-AUDIT-V2.json").read_bytes();f=json.loads(raw)
    for field,name in (("audit_source_sha256","audit_a04_v2.py"),("test_source_sha256","test_a04_v2.py")):
        need(hashlib.sha256((HERE/name).read_bytes()).hexdigest()==f[field],"audit v2 source hash mismatch: "+name)
    old=load_old();parent,_,_=old.load_frozen()
    need(hashlib.sha256((HERE/"SOURCE/BRIDGE/FREEZE.json").read_bytes()).hexdigest()==f["parent_candidate_freeze_sha256"],"parent freeze hash mismatch")
    need(hashlib.sha256((HERE/"SOURCE/BRIDGE/RAW_A03.json").read_bytes()).hexdigest()==f["parent_raw_sha256"],"parent raw hash mismatch")
    need(hashlib.sha256((HERE/"SOURCE/BRIDGE/RESULT_A03.json").read_bytes()).hexdigest()==f["parent_result_sha256"],"parent result hash mismatch")
    return f
def strict_source_audit(raw,result,freeze,oracle):
    old=load_old()
    events=raw["events"]
    down=next(e for e in events if e.get("event")=="input_admission")
    up=next(e for e in events if e.get("event")=="input_release_measurement")
    owner=raw["owner_records"][0]
    source=owner["per_key_release_measurements"][0]
    projected=up["physical_key_measurement"]
    # Compare corresponding projected/source values before calling the legacy
    # audit, whose `is False` check already rejects one alias independently.
    source_projection={k:value for k,value in source.items() if k!="adapter_edge"}
    projected_projection={k:value for k,value in projected.items() if k!="adapter_edge"}
    need(exact(projected_projection,source_projection),"projected measurement differs by exact JSON type or value")
    need(exact(up.get("owner_cleanup_record"),owner),"projected owner record differs by exact JSON type or value")
    # Legacy gate enforces broader event/bracket/authority semantics. A nested
    # `false` -> `0` mutation may fail earlier there; this v2 exact comparison
    # above rejects it without depending on which gate reports first.
    v=old.strict_source_audit(raw,result,freeze,lambda rows: oracle(rows))
    expected_edge={"edge":"up","status":"CONFIRMED_PHYSICAL_UP","actuation_id":down["physical_key_measurement"]["actuation_id"],
                   "owner_id":down["owner_id"],"intent_token":down["intent_token"],"key":down["key"],
                   "interval":source["bracket"]["physical_up_interval"],"grants_input_authority":False}
    need(exact(projected.get("adapter_edge"),expected_edge),"projected adapter edge differs by exact JSON type or value")
    return {**v,"schema":"map01-v39-perkey-bridge-a04-owner-source-audit-v2","status":"PASS_OWNER_SOURCE_BOUND_EXACT_TYPE_AUDIT"}
def main():
    verify_v2_freeze()
    old=load_old();freeze,raw,result=old.load_frozen();verdict=strict_source_audit(raw,result,freeze,old.load_oracle())
    verdict.update({"candidate_raw_sha256":hashlib.sha256((HERE/"SOURCE/BRIDGE/RAW_A03.json").read_bytes()).hexdigest(),
                    "candidate_result_sha256":hashlib.sha256((HERE/"SOURCE/BRIDGE/RESULT_A03.json").read_bytes()).hexdigest(),
                    "candidate_freeze_sha256":hashlib.sha256((HERE/"SOURCE/BRIDGE/FREEZE.json").read_bytes()).hexdigest(),
                    "audit_source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    rendered=json.dumps(verdict,indent=2,sort_keys=True)+"\n"
    Path(__file__).with_name("AUDIT-V2.json").write_text(rendered,encoding="utf-8",newline="\n")
    print(json.dumps(verdict,sort_keys=True))
if __name__=="__main__":main()
