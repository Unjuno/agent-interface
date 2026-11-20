from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
F = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
RAW = json.loads((HERE / "results/RAW.json").read_text(encoding="utf-8"))
errors = []

def req(ok, label):
    if not ok: errors.append(label)

def blob(rel):
    return subprocess.run(["git", "hash-object", "--no-filters", rel], cwd=ROOT,
                          check=True, capture_output=True, text=True).stdout.strip()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

for rel, expected in F["selected_sources"].items():
    req(blob(rel) == expected, "source_blob:" + rel)
req(blob("research/doom/v39_samekey_repeat_a03_20261005/candidate.py") == F["candidate_blob"],
    "candidate_blob")

for i, stop in enumerate(F["prior_stops"], 1):
    raw_path = HERE / stop["path"]
    req(sha(raw_path) == stop["sha256"], "prior_stop_sha256:" + str(i))
    old = json.loads(raw_path.read_text(encoding="utf-8"))
    req(len(old.get("cases", [])) == 2 and all(c.get("case_status") == "STOP" for c in old["cases"]),
        "prior_stop_preserved:" + str(i))
    if i == 1:
        req(all(c.get("error_type") == "ModuleNotFoundError" and not c.get("partial") for c in old["cases"]),
            "a01_preaction_stop")
    else:
        req(all(c.get("error_type") == "AttributeError" and c.get("partial") for c in old["cases"]),
            "a02_partial_stop")

v39=(ROOT/"research/doom/map01_overlap_controller_v39.py").read_text(encoding="utf-8")
v15=(ROOT/"research/doom/session_map01_v15.py").read_text(encoding="utf-8")
req("session_map01_v15.py" in v39 and "session_map01_v12.py" in v39, "selector")
req("from doom_owner_thread_release_batch_backend_v1 import Backend as TelemetryBackend" in v15,
    "v15_backend_v1")

cases={x.get("scenario"):x for x in RAW.get("cases",[])}
req(set(cases)=={"sequential","overlapping_duplicate_down"},"case_set")
seq=cases.get("sequential",{}); ov=cases.get("overlapping_duplicate_down",{})

def ins(c): return [x for x in c.get("events",[]) if x.get("event")=="input_admission"]
def ups(c): return [x for x in c.get("events",[]) if x.get("event")=="input_release_transition"]

for name,c in (("sequential",seq),("overlap",ov)):
    req(c.get("case_status")=="RETURNED",name+"_returned")
    req(c.get("backend_class")=="doom_owner_thread_release_batch_backend_v1.Backend",name+"_backend")
    req(c.get("owner_class")=="input_transition_owner_v4.InputOwner",name+"_owner")
    req(c.get("selector_source_verified") is True,name+"_selector")
    req(c.get("fake_physical_after")==[] and c.get("backend_held_after")==[],name+"_final_empty")

sa,su=ins(seq),ups(seq); so=seq.get("operations",[])
req(len(sa)==2 and all(x.get("key")=="F8" for x in sa),"seq_admissions")
req(len(su)==2 and all(x.get("key")=="F8" for x in su),"seq_release_rows")
req(seq.get("key_up_injection_count")==2,"seq_keyup_injections")
req([x.get("release_batch_position") for x in su]==[0,1],"seq_positions")
req(all(x.get("release_batch_size")==2 and x.get("release_batch_complete") is True for x in su),"seq_batch")
receipts=[x.get("owner_thread_keyup_receipt") for x in su]
req(all(isinstance(r,dict) and r.get("server_sync_completed") is True and
        r.get("physical_verification_authoritative") is False for r in receipts),"seq_receipts")
rt=[r.get("owner_keyrelease_started_ns") for r in receipts if isinstance(r,dict)]
req(len(rt)==2 and len(set(rt))==2,"seq_distinct_receipt_times")
req(all(x.get("owner_thread_keyup_receipt_count")==1 for x in su),"seq_receipt_counts")
req(seq.get("keymap_queries_between_ups")==0,"seq_inter_up_query")
req([x.get("op") for x in seq.get("between_up_operations",[])].count("query_keymap")==0,"seq_trace_query")
req(seq.get("fake_display_counts",{}).get("injections")==4,"seq_fake_injection_count")

unmatched=sorted(sa,key=lambda x:x.get("input_ack_ns",-1)); pairs=[]
for rel,rec in sorted(zip(su,receipts),key=lambda pair:pair[1].get("owner_keyrelease_started_ns",-1)):
    t=rec.get("owner_keyrelease_started_ns")
    eligible=[a for a in unmatched if a.get("input_ack_ns",2**63)<t]
    req(rel.get("key")=="F8" and rec.get("key")==rel.get("key"),"pair_key")
    req(rel.get("id")=="cover-samekey-a03-sequential" and rel.get("step")==2 and
        rel.get("intent_token")=="intent-samekey-a03-sequential" and
        rel.get("owner_id")==rec.get("owner_id") and rel.get("intent_token")==rec.get("intent_token"),
        "pair_context")
    req(bool(eligible),"pair_prior_admission")
    if eligible:
        chosen=max(eligible,key=lambda x:x["input_ack_ns"])
        unmatched.remove(chosen); pairs.append((chosen["input_ack_ns"],t))
req(len(pairs)==2 and not unmatched,"seq_unique_bijection")
req(all(pairs[i][1]<pairs[i+1][0] for i in range(len(pairs)-1)),"seq_episode_interval_order")

oa,ou=ins(ov),ups(ov)
req(len(oa)==2 and all(x.get("key")=="F8" for x in oa),"overlap_two_admissions")
req(len(ou)==1 and all(x.get("key")=="F8" for x in ou),"overlap_one_release")
req(ov.get("key_up_injection_count")==1,"overlap_one_keyup_injection")
req(all(x.get("owner_thread_keyup_receipt_count")==1 for x in ou),"overlap_single_receipt")
require_overlap_hold=(len(oa)==2 and len(ou)==1 and ov.get("key_up_injection_count")==1)
req(require_overlap_hold,"overlap_hold_discriminator")

if errors:
    print(json.dumps({"decision":"FAIL_AUDIT","errors":errors},indent=2))
    raise SystemExit(1)
print(json.dumps({"decision":"PASS_REPEAT_JOIN_WITH_OVERLAP_HOLD",
 "sequential_admissions":len(sa),"sequential_release_rows":len(su),
 "unique_ordered_pairs":len(pairs),"inter_up_keymap_queries":seq.get("keymap_queries_between_ups"),
 "overlap_admissions":len(oa),"overlap_release_rows":len(ou),
 "overlap_disposition":"HOLD_NON_BIJECTIVE",
 "scope":"fake source-composition only"},indent=2))
