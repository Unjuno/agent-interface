"""Read-only audit of the pre-input R01 harness failure and cleanup."""
import json
from datetime import datetime
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
report = json.loads((HERE/'result.json').read_text())
attempt = HERE/'attempt'
root = Path('/tmp')
ps = subprocess.run(['ps','-eo','pid,ppid,pgid,stat,comm,args'],text=True,capture_output=True,check=True)
process_rows = []
for line in ps.stdout.splitlines()[1:]:
    fields = line.split(None,5)
    if int(fields[0]) == __import__('os').getpid():
        continue
    if fields[4].lower() in ('xvfb','xterm'):
        process_rows.append(line)
markers = [str(path) for path in (HERE/'attempt/old-owner/mcp').glob('*') if path.exists()]
rows = {
    'status':'PASS_PREINPUT_HARNESS_FAILURE_CLEANUP_SCOPED',
    'failing_raw_status':report.get('status'),
    'failing_raw_error':report.get('error'),
    'failing_raw_exception':report.get('error_type'),
    'xvfb_pid':report.get('xvfb_pid'),
    'xvfb_exit_code':report.get('xvfb_exit_code'),
    'attempt_directory_exists':attempt.exists(),
    'old_mcp_markers':markers,
    'matching_process_rows':process_rows,
    'xvfb_proc_absent':not Path('/proc',str(report.get('xvfb_pid'))).exists(),
    'display_lock_absent':not (root/'.X188-lock').exists(),
    'display_socket_absent':not (root/'.X11-unix/X188').exists(),
    'timestamp_local':datetime.now().astimezone().isoformat(),
}
checks = [
    report.get('status') == 'FAIL' and report.get('error') == 'major_version'
        and report.get('error_type') == 'AttributeError',
    report.get('xvfb_exit_code') == 0,
    not attempt.exists() and not markers,
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
