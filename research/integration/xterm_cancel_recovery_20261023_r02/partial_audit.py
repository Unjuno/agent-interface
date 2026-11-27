"""Read-only audit of the pre-xterm R02 runner failure and cleanup."""
import json
from datetime import datetime
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
report = json.loads((HERE/'result.json').read_text())
ps = subprocess.run(['ps','-eo','pid,ppid,pgid,stat,comm,args'],text=True,capture_output=True,check=True)
process_rows = []
for line in ps.stdout.splitlines()[1:]:
    fields = line.split(None,5)
    if int(fields[0]) == os.getpid():
        continue
    if fields[4].lower() in ('xvfb','xterm'):
        process_rows.append(line)
attempt = HERE/'attempt'
rows = {
    'status':'PASS_PRE_XTERM_HARNESS_FAILURE_CLEANUP_SCOPED',
    'failing_raw_status':report.get('status'),
    'failing_raw_error':report.get('error'),
    'failing_raw_exception':report.get('error_type'),
    'xvfb_pid':report.get('xvfb_pid'),
    'xvfb_exit_code':report.get('xvfb_exit_code'),
    'attempt_directory_exists':attempt.exists(),
    'old_xterm_base_exists':(attempt/'old-xterm').exists(),
    'old_mcp_directory_exists':(attempt/'old-owner/mcp').exists(),
    'matching_process_rows':process_rows,
    'xvfb_proc_absent':not Path('/proc',str(report.get('xvfb_pid'))).exists(),
    'display_lock_absent':not Path('/tmp/.X188-lock').exists(),
    'display_socket_absent':not Path('/tmp/.X11-unix/X188').exists(),
    'timestamp_local':datetime.now().astimezone().isoformat(),
}
checks = [
    report.get('status') == 'FAIL' and report.get('error_type') == 'FileNotFoundError',
    report.get('xvfb_exit_code') == 0,
    not rows['old_xterm_base_exists'] and not rows['old_mcp_directory_exists'],
    rows['xvfb_proc_absent'] and rows['display_lock_absent'] and rows['display_socket_absent'],
    not process_rows,
    'old_app' not in report and 'old_input_response' not in report,
]
if not all(checks):
    rows['status'] = 'FAIL_PARTIAL_CLEANUP_AUDIT'
rows['checks'] = [bool(value) for value in checks]
(HERE/'cleanup-recheck.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
print(json.dumps(rows,indent=2,sort_keys=True))
if not all(checks):
    raise SystemExit(1)
