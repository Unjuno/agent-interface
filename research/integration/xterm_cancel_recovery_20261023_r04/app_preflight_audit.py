"""Independent audit of both input-free xterm setup attempts."""
import hashlib
import json
from datetime import datetime
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
failed_log=HERE/'preflight-attempt/xterm.log'
failed_text=failed_log.read_text(errors='replace')
failure={
    'status':'FAIL_PREFLIGHT_DISPLAY_MISMATCH',
    'display_server':':189',
    'xterm_environment_display':':188',
    'xterm_log':'preflight-attempt/xterm.log',
    'xterm_log_sha256':hashlib.sha256(failed_log.read_bytes()).hexdigest(),
    'xterm_log_text':failed_text,
    'runner_exit_code':1,
    'surfaced_exception':'Xlib.error.ConnectionClosedError in observer.close after Xvfb teardown; earlier mapped-window wait failure was masked by cleanup ordering.',
    'input_calls':0,
    'task_effects':0,
    'preflight_journal_exists':(HERE/'preflight-journal.jsonl').exists(),
    'display_lock_absent':not Path('/tmp/.X189-lock').exists(),
    'display_socket_absent':not Path('/tmp/.X11-unix/X189').exists(),
    'timestamp_local':datetime.now().astimezone().isoformat(),
}
(HERE/'preflight-r01-failure.json').write_text(json.dumps(failure,indent=2,sort_keys=True)+'\n')

report_path=HERE/'preflight-r02.json'
report=json.loads(report_path.read_text())
current=subprocess.run(['ps','-eo','pid,ppid,pgid,stat,comm,args'],text=True,capture_output=True,check=True)
process_rows=[]
for line in current.stdout.splitlines()[1:]:
    fields=line.split(None,5)
    if fields[4].lower() in ('xvfb','xterm'):
        process_rows.append(line)
checks={
    'prior_display_mismatch_preserved':failure['status']=='FAIL_PREFLIGHT_DISPLAY_MISMATCH'
        and ':188' in failed_text and failure['input_calls']==0 and failure['task_effects']==0,
    'actual_xterm_class_and_interactive_pty':report['status']=='PASS_XTERM_MAPPED_INTERACTIVE_PTY_NO_INPUT'
        and report['window']['wm_class'][1]=='XTerm'
        and report['mapped_xterm_with_interactive_pty'] is True
        and report['direct_children'][0]['stdin_tty'].startswith('/dev/pts/'),
    'preflight_no_input_or_effect':report['input_calls']==0 and report['task_effects']==0
        and report['journal_exists_without_input'] is False
        and report['journal_exists_after_cleanup'] is False
        and set(bytes.fromhex(report['keymap_hex']))=={0},
    'private_process_cleanup':report['xterm_exit_code']==15 and report['xvfb_exit_code']==0
        and not report['xterm_remaining_session_pids'] and not report['xvfb_remaining_session_pids']
        and report['display_lock_absent'] and report['display_socket_absent']
        and not report['cleanup_errors'] and not process_rows,
    'frozen_report_digest_matches_conditions':hashlib.sha256(report_path.read_bytes()).hexdigest()
        ==json.loads((HERE/'conditions.json').read_text())['app_preflight_sha256'],
}
result={'status':'PASS_XTERM_PREFLIGHT_AUDIT' if all(checks.values()) else 'FAIL_XTERM_PREFLIGHT_AUDIT',
    'checks':checks,'preflight_report_sha256':hashlib.sha256(report_path.read_bytes()).hexdigest(),
    'preflight_failure_record':failure,'current_matching_processes':process_rows,
    'timestamp_local':datetime.now().astimezone().isoformat()}
(HERE/'preflight-audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,indent=2,sort_keys=True))
if not all(checks.values()):
    raise SystemExit(1)
