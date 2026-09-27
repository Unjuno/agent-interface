import hashlib
import base64
import json
import os
import subprocess
from pathlib import Path

authority = Path('/tmp/Xauthority')
subprocess.run(['xauth', '-f', str(authority), 'add', os.environ['DISPLAY'], 'MIT-MAGIC-COOKIE-1', os.environ['X11_COOKIE']], check=True, capture_output=True)
os.environ['XAUTHORITY'] = str(authority)

visible = {}
for process in Path('/proc').iterdir():
    if process.name.isdigit():
        try:
            visible[process.name] = (process / 'cmdline').read_bytes().replace(b'\0', b' ').decode('utf-8', 'replace').strip()
        except OSError:
            pass
paths = ['/opt/arena/arena.py', '/opt/arena/engine.py', '/evidence/report.json', '/workspace/arena.py']
display = os.environ['DISPLAY']
info = subprocess.run(['xdpyinfo', '-display', display], capture_output=True, text=True, timeout=5)
windows = subprocess.run(['xwininfo', '-display', display, '-root', '-tree'], capture_output=True, text=True, timeout=5)
window_id = next((line.strip().split()[0] for line in windows.stdout.splitlines() if 'Procedural Control Arena v0' in line), None)
if not window_id:
    raise SystemExit('STOP: arena window not found')
capture = subprocess.run(['xwd', '-display', display, '-root', '-silent', '-out', '/tmp/screen.xwd'], capture_output=True, timeout=5)
raw = Path('/tmp/screen.xwd').read_bytes()
key = subprocess.run(['xdotool', 'key', '--clearmodifiers', '--window', window_id, 'w'], capture_output=True, text=True, timeout=5)
result = {
    'proc_cmdlines': visible,
    'path_access': {path: os.path.exists(path) for path in paths},
    'xdpyinfo_exit': info.returncode,
    'window_tree': windows.stdout,
    'window_id': window_id,
    'capture_exit': capture.returncode,
    'capture_bytes': len(raw),
    'capture_sha256': hashlib.sha256(raw).hexdigest(),
    'capture_header_size': int.from_bytes(raw[:4], 'big') if len(raw) >= 4 else 0,
    'key_exit': key.returncode,
    'key_stdout': key.stdout,
    'key_stderr': key.stderr,
    'key_action': 'w',
}
Path('/tmp/controller-probe.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result, sort_keys=True))
print('XWD_BASE64:' + base64.b64encode(raw).decode('ascii'))
if info.returncode or capture.returncode or key.returncode:
    raise SystemExit(2)
