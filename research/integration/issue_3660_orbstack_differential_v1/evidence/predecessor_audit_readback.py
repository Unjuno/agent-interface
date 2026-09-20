"""Post-result independent recomputation; never mutates the formal result."""
import hashlib, json, sys
from pathlib import Path

raw_path=Path(sys.argv[1])
raw_bytes=raw_path.read_bytes(); raw=json.loads(raw_bytes)
events=raw["ledger"]
errors=[]
def event(kind):
    found=[e for e in events if e.get("kind")==kind]
    if len(found)!=1: errors.append(f"{kind}: expected one event, found {len(found)}")
    return found[0] if len(found)==1 else {}

if [e.get("seq") for e in events]!=list(range(len(events))): errors.append("sequence discontinuity")
for e in events:
    payload=dict(e); claimed=payload.pop("hash",None)
    if hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()!=claimed:
        errors.append(f"event hash mismatch:{e.get('seq')}")
apps=raw.get("apps",{})
if set(apps)!={"inkscape","calc","chromium"}: errors.append("application set mismatch")
windows={}
for role,info in apps.items():
    identity=info.get("identity",{}); matches=identity.get("matches",[])
    if identity.get("status")!="READY" or len(matches)!=1: errors.append(f"{role}: not unique READY")
    elif str(info.get("window"))!=str(matches[0].get("window")): errors.append(f"{role}: resolved window mismatch")
    else: windows[role]=str(info["window"])
if len(set(windows.values()))!=3: errors.append("initial XIDs not distinct")

drift=event("focus_drift"); stale=event("stale_admission")
focus_ok=(drift.get("from_app")=="calc" and drift.get("to_app")=="inkscape" and
          drift.get("active")==windows.get("inkscape") and drift.get("active")!=windows.get("calc") and
          drift.get("input_emitted") is False and stale.get("old_window")==windows.get("calc") and
          stale.get("disposition")=="refused" and stale.get("input_emitted") is False)
modal=event("modal_transition"); recovery=event("modal_recovery")
modal_ok=(modal.get("app")=="calc" and modal.get("parent")==windows.get("calc") and modal.get("modal") and
          modal.get("input_emitted") is True and recovery.get("modal")==modal.get("modal") and
          recovery.get("disposition")=="observe_only" and recovery.get("input_emitted") is True)
geometry=event("geometry_transition"); stale_geom=event("stale_geometry_admission")
geometry_ok=(geometry.get("app")=="calc" and geometry.get("old_geometry")!=geometry.get("new_geometry") and
             geometry.get("surface_generation")==2 and stale_geom.get("disposition")=="refused" and
             stale_geom.get("input_emitted") is False)
replacement=event("window_replacement"); stale_window=event("stale_window_admission")
replacement_ok=(replacement.get("app")=="chromium" and replacement.get("old_window")==replacement.get("new_window") and
                replacement.get("identity_reused") is True and replacement.get("old_pid")!=replacement.get("new_pid") and
                replacement.get("surface_generation")==2 and
                not replacement.get("old_process_cleanup",{}).get("remaining_pids") and
                stale_window.get("old_window")==replacement.get("old_window") and
                stale_window.get("disposition")=="refused" and stale_window.get("input_emitted") is False)
returned=event("return_to_earlier_app"); stable=event("stable_control")
return_ok=(returned.get("app")=="calc" and returned.get("window")==windows.get("calc") and
           returned.get("surface_generation")==2 and returned.get("fresh_validation") is True and
           stable.get("action_dispatched") is False and stable.get("independent_task_effect_scored") is False)
checks={"focus_drift_stale_refusal":focus_ok,"modal_observe_recovery":modal_ok,
        "geometry_change_stale_refusal":geometry_ok,"chromium_replacement_generation_stale_refusal":replacement_ok,
        "return_to_prior_app_fresh_validation":return_ok}
for name,value in checks.items():
    if not value: errors.append("recomputed check failed:"+name)
if raw.get("checks")!=list(checks.values()): errors.append("runner check vector differs from recomputation")
if raw.get("transition_gate")!="PASS_MIXED_APP_READINESS_TRANSITIONS_SCOPED": errors.append("transition disposition mismatch")
if raw.get("decision")!="HOLD_TASK_EFFECT_UNTESTED" or raw.get("independent_task_effect_scored") is not False: errors.append("scope disposition mismatch")
if raw.get("model_calls")!=0 or raw.get("network_calls")!=0: errors.append("unexpected model/network call count")
cleanup=event("process_cleanup")
if cleanup.get("complete") is not True or raw.get("cleanup_complete") is not True: errors.append("cleanup not complete")
if not raw.get("xvfb_socket_disappeared"): errors.append("Xvfb socket remains")
if any(p.get("remaining_pids") for p in raw.get("cleanup_processes",[]) if p): errors.append("process group survivors")
if not any(p.get("returncode")==255 for p in raw.get("cleanup_processes",[]) if p): errors.append("recorded LO teardown code 255 missing")
out={"decision":"PASS_POSTHOC_EVENT_RECOMPUTATION" if not errors else "HOLD_POSTHOC_EVENT_RECOMPUTATION",
     "error_count":len(errors),"errors":errors,"recomputed_checks":checks,
     "raw_result_sha256":hashlib.sha256(raw_bytes).hexdigest(),"xid_reused":replacement.get("identity_reused"),
     "old_pid":replacement.get("old_pid"),"new_pid":replacement.get("new_pid"),
     "libreoffice_teardown_returncode":255,"task_effect":"NOT_TESTED"}
print(json.dumps(out,sort_keys=True,indent=2))
if errors: raise SystemExit(1)
