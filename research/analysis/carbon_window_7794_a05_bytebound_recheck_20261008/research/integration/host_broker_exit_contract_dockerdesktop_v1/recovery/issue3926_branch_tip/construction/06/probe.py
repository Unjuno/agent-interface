from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

STUDY = Path('/study')
OUT = Path(os.environ.get('OUT_DIR', '/out'))
fake_source = (STUDY / 'fake_codex.py').read_bytes()
broker_source = Path('/source/runtime/host_model_ipc_broker_v1.py').read_bytes()
for name, source in [('fake_codex.py', fake_source),
                     ('host_model_ipc_broker_v1.py', broker_source)]:
    compile(source, name, 'exec')
fake = Path('/tmp/construction-fake-codex')
fake.write_bytes(fake_source)
fake.chmod(0o755)
capture = OUT / 'fake-capture.json'
OUT.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
env.update({'FAKE_CAPTURE_PATH': str(capture), 'FAKE_EXIT': '0', 'FAKE_SLEEP_S': '0'})
proc = subprocess.run([str(fake)], input='construction-only\n', text=True,
                      capture_output=True, env=env, timeout=5)
result = {
    'classification': 'PASS_FAKE_ONLY_CONTAINER_CONSTRUCTION' if proc.returncode == 0 else 'STOP',
    'engine_version_expected_by_host': '29.8.0',
    'broker_sha256': hashlib.sha256(broker_source).hexdigest(),
    'fake_sha256': hashlib.sha256(fake_source).hexdigest(),
    'python': sys.version, 'platform': platform.platform(), 'machine': platform.machine(),
    'fake_exit': proc.returncode, 'fake_stdout': proc.stdout, 'fake_stderr': proc.stderr,
    'fake_capture': json.loads(capture.read_text(encoding='utf-8')) if capture.exists() else None,
}
(OUT / 'construction.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if proc.returncode == 0 else 1)
