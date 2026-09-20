"""Independent audit of the one-shot readiness/session ledger."""
import hashlib, json, os
from pathlib import Path

raw=json.loads(Path("/input/result.json").read_text())
errors=[]
def sha(data): return hashlib.sha256(data).hexdigest()
freeze_bytes=Path("/freeze.json").read_bytes(); manifest_bytes=Path("/source_manifest.json").read_bytes(); prereg=Path("/preregistration.md").read_bytes()
freeze=json.loads(freeze_bytes); manifest=json.loads(manifest_bytes)
if raw.get("allocation_id")!="issue2499-readiness-successor-3634-formal-01" or raw.get("issue")!=3645: errors.append("allocation identity mismatch")
if raw.get("formal_invocations")!=1 or raw.get("retries")!=0: errors.append("formal invocation accounting mismatch")
if raw.get("freeze_sha256")!=sha(freeze_bytes) or raw.get("source_manifest_sha256")!=sha(manifest_bytes): errors.append("freeze/manifest hash mismatch")
if raw.get("preregistration_sha256")!=sha(prereg) or freeze.get("preregistration_sha256")!=sha(prereg): errors.append("preregistration hash mismatch")
if raw.get("source_commit")!=freeze.get("source_commit") or manifest.get("source_commit")!=freeze.get("source_commit"): errors.append("source commit mismatch")
if raw.get("image_id")!=freeze.get("image_id") or raw.get("platform")!="linux/arm64": errors.append("image/platform binding mismatch")
for name,digest in manifest.get("files",{}).items():
    p=Path("/src")/name
    if not p.is_file() or sha(p.read_bytes())!=digest: errors.append("source hash mismatch:"+name)
events=raw.get("ledger",[])
if not events: errors.append("ledger missing")
if [e.get("seq") for e in events]!=list(range(len(events))): errors.append("event sequence gap")
for e in events:
    payload=dict(e); claimed=payload.pop("hash",None)
    actual=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
    if claimed!=actual: errors.append(f"event hash mismatch:{e.get('seq')}")
kind=[e.get("kind") for e in events]
is_stop=raw.get("decision")=="STOP_MIXED_APP_READINESS_SUCCESSOR"
setup=next((e for e in events if e.get("kind")=="session_setup"),{})
if setup.get("xauthority_cookie_added") is not True or setup.get("xauthority_mode")!="cookie_auth_file":
    errors.append("formal Xauthority cookie provenance missing")
required={"session_setup","stop","process_cleanup"} if is_stop else {"session_setup","observe","focus_drift","stale_admission","modal_transition","modal_recovery",
          "geometry_transition","stale_geometry_admission","window_replacement","stale_window_admission",
          "return_to_earlier_app","stable_control","process_cleanup"}
missing=sorted(required-set(kind))
if missing: errors.append("missing events:"+",".join(missing))
apps=raw.get("apps",{})
if not is_stop and set(apps)!={"inkscape","calc","chromium"}: errors.append("app identity set mismatch")
for name,info in apps.items():
    identity=info.get("identity",{})
    if identity.get("status")!="READY" or len(identity.get("matches",[]))!=1:
        errors.append(f"{name}: identity not exactly-one READY")
    if str(info.get("window")) not in [str(r.get("window")) for r in identity.get("matches",[])]:
        errors.append(f"{name}: admitted window differs from resolved role")
    if not info.get("pid"): errors.append(f"{name}: launch pid missing")
if is_stop:
    if raw.get("transition_gate")!="NOT_RUN_OR_INCOMPLETE": errors.append("STOP transition disposition mismatch")
    if raw.get("session_complete") is not False: errors.append("STOP marked complete")
    if "stop" not in kind: errors.append("STOP record missing")
else:
    if raw.get("transition_gate")!="PASS_MIXED_APP_READINESS_TRANSITIONS_SCOPED": errors.append("transition gate not PASS")
    if raw.get("decision")!="HOLD_TASK_EFFECT_UNTESTED": errors.append("overall scope disposition mismatch")
    if not all(raw.get("checks",[])) or len(raw.get("checks",[]))!=5: errors.append("transition checks incomplete")
if raw.get("independent_task_effect_scored") is not False: errors.append("unsupported task-effect claim")
if raw.get("model_calls")!=0 or raw.get("network_calls")!=0: errors.append("unexpected model/network activity")
if not raw.get("cleanup_complete"): errors.append("process/socket cleanup incomplete")
for proc in raw.get("cleanup_processes",[]):
    if proc is None or proc.get("returncode") is None or proc.get("remaining_pids"):
        errors.append("process group not reconciled")
if not raw.get("xvfb_socket_disappeared"): errors.append("Xvfb socket remains")
result={"decision":("PASS_AUDITED_EARLY_STOP" if is_stop else "PASS_READINESS_TRANSITIONS_AUDITED") if not errors else "HOLD_READINESS_TRANSITIONS_AUDIT",
        "error_count":len(errors),"errors":errors,"event_count":len(events),
        "raw_sha256":sha(Path("/input/result.json").read_bytes()),
        "task_effect_scope":"NOT_TESTED","model_calls":raw.get("model_calls"),
        "network_calls":raw.get("network_calls")}
Path(os.environ["AUDIT_OUTPUT"]).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps(result,sort_keys=True))
if errors: raise SystemExit(1)
