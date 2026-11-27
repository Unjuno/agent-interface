"""Independent no-input xterm preflight checks for R05."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
p=HERE/'preflight-r05.json'
b=p.read_bytes(); r=json.loads(b)
checks={
 'mapped xterm PTY': r.get('status')=='PASS_XTERM_MAPPED_INTERACTIVE_PTY_NO_INPUT' and r.get('mapped_xterm_with_interactive_pty') is True,
 'no input, task effect, or held key': r.get('input_calls')==0 and r.get('task_effects')==0 and not any(bytes.fromhex(r['keymap_hex'])) and not r.get('journal_exists_after_cleanup'),
 'xterm and Xvfb exited with no session residue': r.get('xterm_exit_code')==15 and r.get('xvfb_exit_code')==0 and not r.get('xterm_remaining_session_pids') and not r.get('xvfb_remaining_session_pids') and not r.get('cleanup_errors'),
 'private display resources cleaned': r.get('display_lock_absent') is True and r.get('display_socket_absent') is True,
}
out={'status':'PASS_R05_PREFLIGHT' if all(checks.values()) else 'FAIL_R05_PREFLIGHT','checks':checks,'report_sha256':hashlib.sha256(b).hexdigest()}
(HERE/'preflight-audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2))
if not all(checks.values()): raise SystemExit(1)
