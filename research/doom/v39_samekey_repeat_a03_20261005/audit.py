from __future__ import annotations
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
F = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
RAW = json.loads((HERE / "results/RAW.json").read_text(encoding="utf-8"))
errors = []

def req(ok, label):
    if not ok:
        errors.append(label)

def blob(rel):
    return subprocess.run(["git", "hash-object", "--no-filters", rel], cwd=ROOT,
                          check=True, capture_output=True, text=True).stdout.strip()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

for rel, expected in F["selected_sources"].items():
    req(blob(rel) == expected, "source_blob:" + rel)
req(blob("research/doom/v39_samekey_repeat_a03_20261005/candidate.py") == F["candidate_blob"],
    "candidate_blob")

old_paths = [
    ("previous_a01_STOP_RAW.json", F["prior_stops"][0]["sha256"], "ModuleNotFoundError", False),
    ("previous_a02_STOP_RAW.json", F["prior_stops"][1]["sha256"], "AttributeError", True),
]
for name, expected, error_type, has_partial in old_paths:
    p = HERE / "results" / name
    req(sha(p) == expected, name + "_sha256")
    old = json.loads(p.read_text(encoding="utf-8"))
    req(len(old.get("cases", [])) == 2, name + "_case_count")
    req(all(x.get("case_status") == "STOP" and x.get("error_type") == error_type
            and bool(x.get("partial")) is has_partial for x in old.get("cases", [])),
        name + "_stop_preserved")

v39 = (ROOT / "research/doom/map01_overlap_controller_v39.py").read_text(encoding="utf-8")
v15 = (ROOT / "research/doom/session_map01_v15.py").read_text(encoding="utf-8")
req("session_map01_v15.py" in v39 and "session_map01_v12.py" in v39, "v39_selector")
req("from doom_owner_thread_release_batch_backend_v1 import Backend as TelemetryBackend" in v15,
    "v15_backend_v1")

cases = RAW.get("cases", [])
req(len(cases) == 2, "case_count")
seq = cases[0] if len(cases) > 0 else {}
overlap = cases[1] if len(cases) > 1 else {}

def admissions(case):
    return [e for e in case.get("events", []) if e.get("event") == "input_admission"]

def releases(case):
    return [e for e in case.get("events", []) if e.get("event") == "input_release_transition"]

for label, case, expected_id in (
    ("sequential", seq, "cover-samekey-a03-sequential"),
    ("overlap", overlap, "cover-samekey-a03-overlapping_duplicate_down"),
):
    req(case.get("case_status") == "RETURNED", label + "_returned")
    req(case.get("backend_class") == "doom_owner_thread_release_batch_backend_v1.Backend",
        label + "_backend_identity")
    req(case.get("owner_class") == "input_transition_owner_v4.InputOwner", label + "_owner_identity")
    req(case.get("selector_source_verified") is True, label + "_selector")
    req(any(e.get("id") == expected_id for e in case.get("events", [])), label + "_source_context")
    req(case.get("fake_physical_after") == [] and case.get("backend_held_after") == [],
        label + "_final_empty")

sa, sr = admissions(seq), releases(seq)
ops = seq.get("operations", [])
req(len(sa) == 2 and all(e.get("key") == "F8" for e in sa), "sequential_two_admissions")
req(len(sr) == 2 and all(e.get("key") == "F8" for e in sr), "sequential_two_release_rows")
req(seq.get("key_up_injection_count") == 2 and
    sum(e.get("op") == "key-up" for e in ops) == 2, "sequential_two_fake_ups")
req(seq.get("keymap_queries_between_ups") == 0 and
    sum(e.get("op") == "query_keymap" for e in seq.get("between_up_operations", [])) == 0,
    "sequential_no_inter_up_query")
req(seq.get("fake_display_counts", {}).get("injections") == 4, "sequential_four_injections")
req([e.get("release_batch_position") for e in sr] == [0, 0], "sequential_single_row_batch_positions")
req([e.get("release_batch_delivery_position") for e in sr] == [0, 1],
    "sequential_delivery_order")
req(all(e.get("release_batch_size") == 1 and e.get("release_batch_complete") is True for e in sr),
    "sequential_complete_single_row_batches")
receipts = [e.get("owner_thread_keyup_receipt") for e in sr]
req(all(isinstance(r, dict) and r.get("event") == "owner_explicit_keyup" and
        r.get("server_sync_completed") is True and
        r.get("physical_verification_authoritative") is False for r in receipts),
    "sequential_identity_bound_receipts")
receipt_times = [r.get("owner_keyrelease_started_ns") for r in receipts if isinstance(r, dict)]
req(len(receipt_times) == 2 and len(set(receipt_times)) == 2, "sequential_distinct_receipt_times")
req(all(e.get("owner_thread_keyup_receipt_count") == 1 for e in sr), "sequential_one_receipt_each")

# Greedily match each ordered release to the latest previously acknowledged unmatched admission.
unmatched = sorted(sa, key=lambda e: e.get("input_ack_ns", -1))
pairs = []
for rel, receipt in sorted(zip(sr, receipts), key=lambda p: p[1].get("owner_keyrelease_started_ns", -1)):
    t = receipt.get("owner_keyrelease_started_ns")
    eligible = [a for a in unmatched if a.get("input_ack_ns", 2**63) < t]
    req(rel.get("key") == receipt.get("key") == "F8", "sequential_pair_key")
    req(rel.get("id") == "cover-samekey-a03-sequential" and rel.get("step") == 2 and
        rel.get("intent_token") == "intent-samekey-a03-sequential" and
        rel.get("owner_id") == receipt.get("owner_id") and
        rel.get("intent_token") == receipt.get("intent_token"), "sequential_pair_context")
    req(bool(eligible), "sequential_prior_admission")
    if eligible:
        chosen = max(eligible, key=lambda a: a["input_ack_ns"])
        unmatched.remove(chosen)
        pairs.append((chosen["input_ack_ns"], t))
req(len(pairs) == 2 and not unmatched, "sequential_bijection")
req(pairs[0][0] < pairs[0][1] < pairs[1][0] < pairs[1][1],
    "sequential_episode_interval_order")

oa, ou = admissions(overlap), releases(overlap)
o_ops = overlap.get("operations", [])
req(len(oa) == 2 and all(e.get("key") == "F8" for e in oa), "overlap_two_admissions")
req(len(ou) == 1 and ou[0].get("key") == "F8", "overlap_single_release_row")
req(overlap.get("key_up_injection_count") == 1 and
    sum(e.get("op") == "key-up" for e in o_ops) == 1, "overlap_single_fake_up")
orec = ou[0].get("owner_thread_keyup_receipt", {}) if ou else {}
req(ou[0].get("owner_thread_keyup_receipt_count") == 1 if ou else False,
    "overlap_single_receipt")
req(orec.get("event") == "owner_explicit_keyup" and orec.get("key") == "F8",
    "overlap_receipt_identity")
req(len(oa) > len(ou) and len(ou) == 1, "overlap_non_bijective_holds")

if errors:
    print(json.dumps({"decision": "FAIL_AUDIT", "errors": errors}, indent=2))
    raise SystemExit(1)
print(json.dumps({
    "decision": "PASS_REPEAT_JOIN_WITH_OVERLAP_HOLD",
    "sequential_admissions": len(sa),
    "sequential_release_rows": len(sr),
    "unique_ordered_pairs": len(pairs),
    "release_batches": [e.get("release_batch_size") for e in sr],
    "inter_up_keymap_queries": seq.get("keymap_queries_between_ups"),
    "overlap_admissions": len(oa),
    "overlap_release_rows": len(ou),
    "overlap_disposition": "HOLD_NON_BIJECTIVE",
    "scope": "fake current-main V39/V15 source composition only"
}, indent=2))
