"""Corrected independent offline audit: separate baseline calls from inspect."""
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); errors=[]
def read(p):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception as e:errors.append(f'{p.name}: unreadable {type(e).__name__}');return {}
r=read(root/'result.json');t=r.get('trace',{});initial=read(root/'initial-identities.json')
old=next((x for x in initial if x.get('name')=='chromium'),{});new=t.get('replacement',{});calls=t.get('calls',[]);inspect=t.get('inspect_replacement',{});sess=t.get('session_after_inspect',{});close=t.get('close',{})
base=calls[:3]
if len(base)!=3 or any(x.get('operation')!='observe' for x in base):errors.append('first three calls are not baseline observations')
sessions={x.get('session',{}).get('session_id') for x in base}
if len(sessions)!=1 or None in sessions:errors.append('baseline session IDs inconsistent')
if len(calls)!=4 or calls[3].get('operation')!='inspect_target':errors.append('call order is not observe×3 then inspect')
if not(old.get('window_id')==t.get('initial_target',{}).get('window_id')):errors.append('initial Chromium identity mismatch')
if not(new.get('window_id')!=old.get('window_id') and new.get('launcher_pid')!=old.get('launcher_pid') and new.get('owner_pid')!=old.get('owner_pid')):errors.append('replacement identity not distinct in XID/launcher/owner PID')
if t.get('old_window_gone') is not True:errors.append('old Chromium window remains')
if inspect.get('status')!='needs_review' or inspect.get('review_id') or 'outside configured transient family' not in inspect.get('error',''):errors.append('replacement inspect did not fail closed')
if sess.get('targets',{}).get('chromium')!=old.get('window_id') or sess.get('binding_revision')!=1:errors.append('server target/revision changed despite failed inspection')
if close.get('status')!='closed' or close.get('release_attempted') is not False:errors.append('unexpected close/release status')
if t.get('server_pids_after_transport'):errors.append('MCP server survived transport shutdown')
decision='FAIL_RAW_AUDIT' if errors else ('HOLD_OLD_LAUNCHER_LIVENESS_UNVERIFIED' if t.get('old_launcher_pid_alive') is True else 'PASS_RAW_AUDIT_SCOPED')
audit={'schema':'agent-interface/2907-public-mcp-root-replacement-audit-v1','decision':decision,'errors':errors,'formal_allocation':False,'checks':{'baseline_observations':len(base),'session_ids':sorted(sessions),'call_order':[x.get('operation') for x in calls],'old_window_gone':t.get('old_window_gone'),'old_launcher_pid_present_after_wait':t.get('old_launcher_pid_alive'),'old_launcher_process_state_recorded':False,'replacement_xid_distinct':new.get('window_id')!=old.get('window_id'),'replacement_launcher_pid_distinct':new.get('launcher_pid')!=old.get('launcher_pid'),'replacement_owner_pid_distinct':new.get('owner_pid')!=old.get('owner_pid'),'inspect_status':inspect.get('status'),'inspect_error':inspect.get('error'),'review_id_present':bool(inspect.get('review_id')),'dispatch_calls':sum(x.get('operation')=='dispatch' for x in calls),'binding_revision_after':sess.get('binding_revision'),'target_after':sess.get('targets',{}).get('chromium'),'close_status':close.get('status'),'release_attempted':close.get('release_attempted'),'mcp_server_after_shutdown':t.get('server_pids_after_transport')},'scope':'one public MCP session; three observations; replacement Chromium PID/XID differs; inspect fails closed; old launcher termination unresolved; not full #2907 integration'}
print(json.dumps(audit,sort_keys=True,indent=2));raise SystemExit(2 if errors else 0)

