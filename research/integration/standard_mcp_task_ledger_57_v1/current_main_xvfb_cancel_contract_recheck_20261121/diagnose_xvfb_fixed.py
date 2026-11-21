import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time

socket_dir = Path('/tmp/.X11-unix')
print('socket_dir_mode', oct(socket_dir.stat().st_mode & 0o7777))
print('existing_sockets', sorted(path.name for path in socket_dir.iterdir()
    if path.is_socket()))
root = Path(tempfile.mkdtemp(prefix='xvfb-fixed-display-'))
authority = root / 'authority'
authority.touch(mode=0o600)
authority.chmod(0o600)
cookie = secrets.token_hex(16)
auth = subprocess.run(['xauth', '-f', str(authority), '-'],
    input=f'add :99 . {cookie}\n', text=True, capture_output=True,
    timeout=5)
print('xauth_exit', auth.returncode, 'stderr', repr(auth.stderr))
proc = subprocess.Popen(['Xvfb', ':99', '-screen', '0', '640x480x24',
    '-nolisten', 'tcp', '-auth', str(authority)], stdout=subprocess.PIPE,
    stderr=subprocess.PIPE)
time.sleep(0.3)
print('xvfb_exit_after_300ms', proc.poll())
if proc.poll() is not None:
    out, err = proc.communicate(timeout=1)
    print('xvfb_stdout', repr(out))
    print('xvfb_stderr', repr(err))
else:
    proc.terminate()
    out, err = proc.communicate(timeout=2)
    print('xvfb_test_exit_after_terminate', proc.returncode)
    print('xvfb_stderr', repr(err))
