"""Independent audit of R03 marker-path failure and isolated cleanup."""
import hashlib
import json
from datetime import datetime
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
report=json.loads((HERE/'result.json').read_text())
owner=HERE/'attempt/old-owner'
fault=json.loads((owner/'xvfb-delayed-request-queued.json').read_text())
sync=json.loads((owner/'xvfb-owner-sync-entered.json').read_text())
release=json.loads((owner/'xvfb-target-release-queued.json').read_text())
requests=[]
for path in owner.glob('*/request.json'):
    row=json.loads(path.read_text())
    if row.get('operation')=='guarded_input':
        requests.append({'path':str(path.relative_to(HERE)),'row':row})
ps=subprocess.run(['ps','-eo','pid,ppid,pgid,stat,comm,args'],text=True,capture_output=True,check=True)
process_rows=[]
for line in ps.stdout.splitlines()[1:]:
    fields=line.split(None,5)
    if fields[4].lower() in ('xvfb','xterm') or fields[2]=='437':
        process_rows.append(line)
tracked=[437,447,448,451]
process_absent={str(pid):not Path('/proc',str(pid)).exists() for pid in tracked}
journal=HERE/'old-journal.jsonl'
checks={
    'formal_attempt_failed_without_relabel':report.get('status')=='FAIL'
        and report.get('error')=='fault injection markers' and report.get('error_type')=='TimeoutError',
    'one_public_input_left_pending_unknown':len(requests)==1
        and requests[0]['row'].get('operation')=='guarded_input'
        and report['old_input_response'].get('status')=='pending'
        and report['old_input_response'].get('effect_status')=='unknown'
        and report['old_input_response'].get('replay_allowed') is False,
    'real_fault_and_UP_queue_were_recorded':fault.get('delay_ms')==8000
        and fault.get('blocked_boundary')=='real python-xlib Display.sync response wait'
        and fault.get('flushed_ns')<=sync.get('entered_ns')
        and release.get('server_release_confirmed') is False
        and release.get('queued_ns')<=sync.get('entered_ns'),
    'cancel_was_not_called_and_owner_close_remained_busy':
        'cancel_invoked_ns' not in report
        and report.get('old_final_close',{}).get('status')=='busy'
        and report.get('old_final_close',{}).get('cleanup_status')=='UNKNOWN',
    'old_task_effect_is_unknown_not_zero_claim':not journal.exists()
        and report.get('old_effect_rows_at_cancel') is None
        and report.get('old_effect_rows_at_horizon') is None,
    'owned_terminal_and_server_cleanup_completed':report['process_cleanup']['old'].get('exit_code')==15
        and not report['process_cleanup']['old'].get('remaining_session_pids')
        and report.get('xvfb_exit_code')==0 and not process_rows
        and all(process_absent.values())
        and not Path('/tmp/.X188-lock').exists()
        and not Path('/tmp/.X11-unix/X188').exists(),
    'runner_watched_wrong_marker_directory':(owner/'xvfb-owner-sync-entered.json').exists()
        and not (owner/'mcp/xvfb-owner-sync-entered.json').exists(),
}
cleanup={
    'status':'PASS_ISOLATED_FAILURE_CLEANUP_AUDIT',
    'failed_run_pid':437,
    'terminated_process_group':437,
    'group_members_observed_before_signal':[437,447,448,451],
    'signal':'SIGTERM to the dedicated trial process group after the runner had saved result.json and exited its async scenario',
    'all_tracked_processes_absent':process_absent,
    'matching_process_rows':process_rows,
    'xvfb_exit_code':report.get('xvfb_exit_code'),
    'display_lock_absent':not Path('/tmp/.X188-lock').exists(),
    'display_socket_absent':not Path('/tmp/.X11-unix/X188').exists(),
    'timestamp_local':datetime.now().astimezone().isoformat(),
}
result={'status':'PASS_R03_FAILURE_RAW_AND_CLEANUP_AUDIT' if all(checks.values()) else 'FAIL_R03_PARTIAL_AUDIT',
    'checks':checks,'old_runtime_task_result':'UNKNOWN; no task-success conclusion was obtained',
    'public_cancel_called':False,'old_task_effect_rows':None,
    'fault_marker':fault,'sync_entry':sync,'target_release_queue':release,
    'input_request':requests[0] if requests else None,
    'cleanup':cleanup,'timestamp_local':datetime.now().astimezone().isoformat()}
(HERE/'cleanup-recheck.json').write_text(json.dumps(cleanup,indent=2,sort_keys=True)+'\n')
(HERE/'partial-audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,indent=2,sort_keys=True))
if not all(checks.values()):
    raise SystemExit(1)
