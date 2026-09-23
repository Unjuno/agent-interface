import json
import os
from pathlib import Path
import select
import subprocess
import sys

root = Path('results-local/native-release-quarantine-03')
root.mkdir(exist_ok=False)
with (root/'xvfb.stderr').open('w') as errors:
    server = subprocess.Popen(['Xvfb', ':19982', '-displayfd', '1', '-screen', '0',
                               '640x360x24', '-nolisten', 'tcp', '-nolisten', 'unix', '-ac'],
                              stdout=subprocess.PIPE, stderr=errors, text=True)
    try:
        if not select.select([server.stdout], [], [], 10)[0]:
            raise RuntimeError('private display readiness timeout')
        number = server.stdout.readline().strip()
        if not number.isdigit() or Path('/tmp/.X11-unix/X'+number).exists():
            raise RuntimeError('private display unavailable or shadowed')
        env = dict(os.environ, DISPLAY=':'+number, XAUTHORITY='', AI_RELEASE_TRACE=str((root/'live-trace.json').resolve()))
        test = subprocess.run([sys.executable, '-m', 'unittest', '-v',
                               'runtime.backends.x11_v1.test_integration', 'runtime.backends.x11_v1.test_partial_execution', 'runtime.cli_v1.test_native_golden_boundary', 'test_native_handle_bridge_v1'],
                              env=env, capture_output=True, text=True, timeout=40)
        (root/'test.stdout').write_text(test.stdout)
        (root/'test.stderr').write_text(test.stderr)
        (root/'result.json').write_text(json.dumps({'returncode': test.returncode, 'display': ':'+number}))
        print(test.stderr)
        if test.returncode:
            raise RuntimeError('live suite failed')
    finally:
        if server.poll() is None:
            server.terminate()
        code = server.wait(timeout=5)
        (root/'cleanup.json').write_text(json.dumps({'pid': server.pid, 'returncode': code}))
