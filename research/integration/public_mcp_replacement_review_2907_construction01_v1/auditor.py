"""Independent offline audit; preserves ambiguity about old launcher liveness."""
import json,sys,hashlib
from pathlib import Path
root=Path(sys.argv[1]); errors=[]
def read(p):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception as e: errors.append(f'{p.name}: unreadable {type(e).__name__}'); return {}
r=read(root/'result.json'); t=r.get('trace',{}); ids=read(root/'initial-identities.json')
original=next((x for x in ids if x.get('name')=='chromium'),{})
new=t.get('replacement',{}); inspection=t.get('inspect_replacement',{}); close=t.get('close',{})
baseline=t.get('calls',[]); sessions={x.get('session',{}).get('session_id') for x in baseline if x.get('session')}
if len(baseline)!=3 or any(x.get('operation')!='observe' for x in baseline):errors.append('baseline observation count/order invalid')
if len(sessions)!=1 or None in sessions:errors.append('baseline session identity inconsistent')
if original.get('window_id')!=t.get('initial_target',{}).get('window_id'):errors.append('initial target identity mismatch')
if not (new.get('window_id')!=original.get('window_id') and new.get('launcher_pid')!=original.get('launcher_pid') and new.get('owner_pid')!=original.get('owner_pid')):errors.append('replacement PID/XID distinction not proven')
if t.get('old_window_gone') is not True:errors.append('old XID disappearance not proven')
if inspection.get('status')!='needs_review' or inspection.get('review_id') or 'outside configured transient family' not in inspection.get('error',''):errors.append('replacement inspection did not fail closed as expected')
sess=t.get('session_after_inspect',{})
if sess.get('targets',{}).get('chromium')!=original.get('window_id') or sess.get('binding_revision')!=1:errors.append('owner target/revision mutated after failed inspect')
if any(x.get('operation')=='dispatch' for x in t.get('calls',[])):errors.append('unexpected dispatch in runner trace')
if close.get('status')!='closed' or close.get('release_attempted') is not False:errors.append('no-input connection close mismatch')
if t.get('server_pids_after_transport'):errors.append('MCP server remains after transport shutdown')
old_alive=t.get('old_launcher_pid_alive')
decision='FAIL_RAW_AUDIT' if errors else ('HOLD_OLD_LAUNCHER_LIVENESS_UNVERIFIED' if old_alive is True else 'PASS_RAW_AUDIT_SCOPED')
audit={'schema':'agent-interface/2907-public-mcp-root-replacement-audit-v1','decision':decision,'errors':errors,'formal_allocation':False,'checks':{'baseline_observations':len(baseline),'session_ids':sorted(sessions),'old_window_gone':t.get('old_window_gone'),'old_launcher_pid_present_after_wait':old_alive,'replacement_xid_distinct':new.get('window_id')!=original.get('window_id'),'replacement_launcher_pid_distinct':new.get('launcher_pid')!=original.get('launcher_pid'),'replacement_owner_pid_distinct':new.get('owner_pid')!=original.get('owner_pid'),'inspect_status':inspection.get('status'),'inspect_error':inspection.get('error'),'review_id_present':bool(inspection.get('review_id')),'dispatch_calls':sum(x.get('operation')=='dispatch' for x in t.get('calls',[])),'binding_revision_after':sess.get('binding_revision'),'target_after':sess.get('targets',{}).get('chromium'),'close_status':close.get('status'),'release_attempted':close.get('release_attempted'),'mcp_server_after_shutdown':t.get('server_pids_after_transport')},'scope':'one public MCP session, three baseline observations, Chromium root replacement and fail-closed inspect; not full #2907 integration'}
print(json.dumps(audit,sort_keys=True,indent=2));raise SystemExit(2 if errors else 0)

