"""Capture read-only native executable, resolved library, and Python identities."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BUNDLE = Path('/home/user/.cache/agent-interface/xterm-20261023-r01/root')
XTERM = BUNDLE/'usr/bin/xterm'
env = dict(os.environ, LD_LIBRARY_PATH=str(BUNDLE/'usr/lib/x86_64-linux-gnu'))
ldd = subprocess.run(['ldd',str(XTERM)],env=env,text=True,capture_output=True,check=True)
(HERE/'ldd-xterm.txt').write_text(ldd.stdout+ldd.stderr)
paths = {'/usr/bin/Xvfb','/usr/bin/xauth','/usr/bin/python3',str(XTERM),
    str(BUNDLE/'usr/lib/x86_64-linux-gnu/libXft.so.2')}
for line in ldd.stdout.splitlines():
    match = re.search(r'=>\s+(/\S+)|^\s*(/\S+)\s+\(',line)
    if match:
        paths.add(match.group(1) or match.group(2))
rows = []
for raw in sorted(paths):
    path = Path(raw)
    real = path.resolve(strict=True)
    rows.append({'path':raw,'realpath':str(real),
        'sha256':hashlib.sha256(real.read_bytes()).hexdigest()})
(HERE/'native-binaries.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
freeze = subprocess.run([sys.executable,'-m','pip','freeze'],text=True,capture_output=True,check=True)
(HERE/'pip-freeze.txt').write_text(freeze.stdout)
print(json.dumps({'status':'READONLY_NATIVE_PREFLIGHT_CAPTURED','binaries':len(rows),
    'python':sys.version.split()[0]},indent=2))
