from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

EVIDENCE_COMMIT = "59e307adde701dc3e061ee3ff124c5982c20fcc9"
SOURCE_HEAD = "2b0cb591c3ebcb84d1db983612613850c08fffea"
PACKAGE = "research/doom/v15_native_x11_59_e0cc_20261005"
EXPECTED_RAW_SHA256 = "923d7ce368cafe7a05b0799d7dbcac5eb39462628099d571c9d2cc4d8d8e3aa6"
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "RESULT.json"
checks: list[dict] = []
def git_bytes(rev: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{rev}:{path}"], cwd=ROOT)
def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
def check(name: str, ok: bool, detail: str) -> None:
    checks.append({"name": name, "pass": bool(ok), "detail": detail})
def load(path: str):
    return json.loads(git_bytes(EVIDENCE_COMMIT, f"{PACKAGE}/{path}"))

manifest_bytes = git_bytes(EVIDENCE_COMMIT, f"{PACKAGE}/manifest.json")
manifest = json.loads(manifest_bytes)
tracked = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", EVIDENCE_COMMIT, "--", PACKAGE], cwd=ROOT).decode().splitlines()
tracked_rel = {p[len(PACKAGE)+1:] for p in tracked}
manifest_paths = {entry["path"] for entry in manifest["files"]}
check("package_manifest_exact_tree", tracked_rel - {"manifest.json"} == manifest_paths, f"tracked={len(tracked_rel)-1}, listed={len(manifest_paths)}")
package_bad=[]
for entry in manifest["files"]:
    data=git_bytes(EVIDENCE_COMMIT, f"{PACKAGE}/{entry['path']}")
    if len(data)!=entry["bytes"] or sha(data)!=entry["sha256"]:
        package_bad.append(entry["path"])
check("all_package_entries_hash_and_size", not package_bad, f"listed={len(manifest_paths)}, bad={package_bad}")

lock_bytes=git_bytes(EVIDENCE_COMMIT, f"{PACKAGE}/source-lock.json")
lock=json.loads(lock_bytes)
source_bad=[]
for entry in lock["files"]:
    path=entry["path"]
    data=git_bytes(SOURCE_HEAD,path)
    blob=subprocess.check_output(["git","rev-parse",f"{SOURCE_HEAD}:{path}"],cwd=ROOT).decode().strip()
    if len(data)!=entry["bytes"] or sha(data)!=entry["sha256"] or blob!=entry["git_blob"]:
        source_bad.append(path)
check("source_lock_exact_git_identity", lock.get("head")==SOURCE_HEAD and len(lock["files"])==81 and not source_bad, f"locked={len(lock['files'])}, bad={source_bad}")
raw_bytes=git_bytes(EVIDENCE_COMMIT,f"{PACKAGE}/run-01/raw.json")
raw=json.loads(raw_bytes)
check("raw_digest_and_embedded_source_lock", sha(raw_bytes)==EXPECTED_RAW_SHA256 and raw.get("source_lock_sha256")==sha(lock_bytes), f"raw_sha256={sha(raw_bytes)}, source_lock_sha256={sha(lock_bytes)}")

run=load("run-01-result.json")
check("recorded_candidate_exit", run.get("exit_code")==0 and run.get("stderr")=="", f"exit={run.get('exit_code')}, stderr={run.get('stderr')!r}")
original_audit=load("run-01/audit.json")
failed=[x.get("name") for x in original_audit.get("checks",[]) if not x.get("pass")]
check("retained_auditor_complete_pass", original_audit.get("pass") is True and len(original_audit.get("checks",[]))==658 and not failed, f"checks={len(original_audit.get('checks',[]))}, failed={failed[:10]}")
mutations=load("run-01/audit-mutations.json")
controls=mutations.get("controls",[])
check("eight_corruption_controls_rejected", mutations.get("pass") is True and len(controls)==8 and all(c.get("rejected") is True for c in controls) and mutations.get("raw_sha256")==EXPECTED_RAW_SHA256, f"controls={len(controls)}, rejected={sum(c.get('rejected') is True for c in controls)}")

# Independent semantic reconstruction from raw fields, not the author's 658-check output.
ordered=raw["cases"]["ordered_batch"]
inverse={v:k for k,v in ordered["keycodes"].items()}
events=ordered["window_events"]
press=[inverse[e["detail"]] for e in events if e["type"]=="KeyPress"]
release=[inverse[e["detail"]] for e in events if e["type"]=="KeyRelease"]
admissions=ordered["admissions"]
backend=ordered["backend_rows"]
owner=ordered["owner_records"]
ids={a["key"]:a["physical_key_measurement"]["actuation_id"] for a in admissions}
identity_ok=True
for row in backend:
    receipt=row.get("owner_thread_keyup_receipt") or {}
    m=receipt.get("physical_key_measurement") or {}
    a=next((a for a in admissions if a["key"]==row.get("key")),{})
    identity_ok &= bool(a) and row.get("owner_identity_matches_after_batch") is True and row.get("owner_transition_verified") is True
    identity_ok &= m.get("actuation_id")==ids.get(row.get("key")) and m.get("edge")=="up"
    identity_ok &= m.get("grants_input_authority") is False and m.get("application_consumption_observed") is False
check("ordered_batch_native_edge_order", press==["a","s","w"] and release==["w","s","a"] and all(e.get("send_event") is False for e in events), f"press={press}, release={release}")
check("ordered_batch_keymaps_neutralize", ordered.get("before")=={"a":False,"s":False,"w":False} and ordered.get("after_down")=={"a":True,"s":True,"w":True} and ordered.get("after_batch")=={"a":False,"s":False,"w":False}, f"before={ordered.get('before')}, after_down={ordered.get('after_down')}, after_batch={ordered.get('after_batch')}")
check("ordered_batch_receipts_keep_admission_identity", [a["key"] for a in admissions]==["a","s","w"] and [r.get("key") for r in backend]==["w","s","a"] and identity_ok, f"admissions={len(admissions)}, batch_rows={len(backend)}, owner_records={len(owner)}")

cancel=raw["cases"]["cancel_cleanup_then_late_up"]
pairs=cancel["cleanup_measurement_identity_pairs"]
pair_ok=True
for key,pair in pairs.items():
    down=pair.get("down") or {}; up=pair.get("cleanup_up") or {}
    pair_ok &= pair.get("same_identity") is True and pair.get("cleanup_basis")=="per_key_cleanup_snapshot"
    pair_ok &= down.get("actuation_id")==up.get("actuation_id") and down.get("key")==key and up.get("key")==key
    pair_ok &= up.get("grants_input_authority") is False and up.get("application_consumption_observed") is False
check("cleanup_preserves_per_key_identity_without_authority", len(pairs)==2 and pair_ok and cancel.get("cleanup_record",{}).get("verified") is True, f"pairs={list(pairs)}, verified={cancel.get('cleanup_record',{}).get('verified')}")
pre_records=cancel.get("owner_records_before_late_up",[])
post_records=cancel.get("owner_records_after_late_up",[])
check("late_up_cancelled_without_new_event_or_owner_record", cancel.get("late_up_exception",{}).get("type")=="Cancelled" and len(cancel.get("window_events",[]))==cancel.get("all_window_event_count_before_late_up")==4 and len(cancel.get("owner_records_before_late_up",[]))==len(post_records)==1 and pre_records==post_records and cancel.get("keys_up_event_count_before_late_up")==2, f"exception={cancel.get('late_up_exception',{}).get('type')}, window_events={len(cancel.get('window_events',[]))}, records={len(pre_records)}->{len(post_records)}")
check("cancel_close_stops_owner_and_leaves_keys_up", cancel.get("after_cleanup_before_late_up")=={"a":False,"s":False} and cancel.get("after_close")=={"a":False,"s":False} and cancel.get("owner_stopped") is True and cancel.get("owner_thread_alive") is False and cancel.get("owner_close_succeeded") is True, f"after_close={cancel.get('after_close')}, stopped={cancel.get('owner_stopped')}, alive={cancel.get('owner_thread_alive')}")

check("xvfb_and_observer_closed", raw.get("xvfb_exit")==0 and raw.get("observer_closed") is True, f"xvfb_exit={raw.get('xvfb_exit')}, observer_closed={raw.get('observer_closed')}")
stop=load("vm-stop.json")
check("owned_vm_stopped_readback", stop.get("exit_code")==0 and stop.get("readback",{}).get("exit_code")==0 and "State: stopped" in stop.get("readback",{}).get("stdout",""), f"stop_exit={stop.get('exit_code')}, readback={stop.get('readback',{}).get('stdout','').splitlines()[:3]}")

result={"schema":"independent-v15-native-x11-raw-audit-a01-v1","classification":"read-only audit of one retained native virtual-X11 construction run; no candidate replay","evidence_commit":EVIDENCE_COMMIT,"source_head":SOURCE_HEAD,"raw_sha256":sha(raw_bytes),"checks":checks,"passed":sum(c["pass"] for c in checks),"total":len(checks),"disposition":"PASS_SCOPED" if all(c["pass"] for c in checks) else "FAIL_OR_REVIEW","limitations":["single run, not reliability evidence","private Xvfb / XTEST virtual server only","driver directly invokes backend batch methods; not V39 or production execute","no game, model, physical keyboard, application effect, useful feedback, recovery, or gameplay result","raw-only audit shares the one archived execution record"]}
OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2,ensure_ascii=False))
if not all(c["pass"] for c in checks): raise SystemExit(1)
