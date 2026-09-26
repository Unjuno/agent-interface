"""Bounded private-display orchestration. Existing output directories are never reused."""
import hashlib
import json
import os
from pathlib import Path
import select
import shutil
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
SCENARIOS = ['fast', 'delayed', 'absent', 'late', 'blocked_fast', 'blocked_absent']
POLICIES = ['PRECHECK_ONLY', 'POST_OBSERVATION']

def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')

def run(out, repetition):
    out.mkdir(parents=True, exist_ok=False)
    if (HERE / 'FREEZE.json').exists():
        freeze = json.loads((HERE / 'FREEZE.json').read_text())
        for name, digest in freeze['source_sha256'].items():
            if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != digest:
                raise RuntimeError('frozen source mismatch: ' + name)
    env = {k:v for k,v in os.environ.items() if k not in ('DISPLAY','XAUTHORITY')}
    errors, rows = [], []
    server = None
    display = None
    with tempfile.TemporaryDirectory(prefix='dwell-private-') as temp:
        auth = Path(temp) / 'auth'
        auth.write_bytes(b'')
        # Xauthority's FamilyWild entry permits the allocated display, not the host display.
        cookie = os.urandom(16)
        fields = [b'', b'', b'MIT-MAGIC-COOKIE-1', cookie]
        auth.write_bytes(b'\xff\xff' + b''.join(len(v).to_bytes(2,'big')+v for v in fields))
        auth.chmod(0o600)
        rfd,wfd = os.pipe()
        server_cmd = [shutil.which('Xvfb'), '-displayfd', str(wfd), '-screen','0','640x480x24',
                      '-nolisten','tcp','-auth',str(auth)]
        with (out/'xvfb.stderr').open('wb') as server_log:
            try:
                server = subprocess.Popen(server_cmd, pass_fds=(wfd,), env=env,
                                          stdout=subprocess.DEVNULL, stderr=server_log)
                os.close(wfd); wfd = -1
                if not select.select([rfd],[],[],5)[0]:
                    raise TimeoutError('Xvfb display allocation')
                display = os.read(rfd,32).decode().strip()
                if not display.isdecimal():
                    raise RuntimeError('invalid display')
                env.update(DISPLAY=':'+display, XAUTHORITY=str(auth), PYTHONDONTWRITEBYTECODE='1')
                for scenario in SCENARIOS:
                    order = POLICIES if repetition % 2 == 0 else POLICIES[::-1]
                    for policy in order:
                        command = [sys.executable,'-B',str(HERE/'worker.py'),policy,scenario]
                        before = time.monotonic_ns()
                        proc = subprocess.run(command, env=env, capture_output=True, timeout=4)
                        row = {'repetition':repetition,'scenario':scenario,'policy':policy,
                               'command':command,'started_ns':before,'ended_ns':time.monotonic_ns(),
                               'returncode':proc.returncode, 'stdout':proc.stdout.decode(),
                               'stderr':proc.stderr.decode()}
                        rows.append(row)
                        with (out/'raw.jsonl').open('a') as f:
                            f.write(json.dumps(row,separators=(',',':'))+'\n'); f.flush()
                        if proc.returncode:
                            raise RuntimeError('worker nonzero exit')
            except BaseException as exc:
                errors.append(type(exc).__name__+': '+str(exc))
            finally:
                os.close(rfd)
                if wfd >= 0:
                    os.close(wfd)
                server_exit = None
                if server is not None:
                    server.terminate()
                    try: server_exit = server.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        server.kill(); server_exit = server.wait(timeout=2)
                        errors.append('Xvfb required kill')
                terminal = {'rows':len(rows),'errors':errors,'server_pid':getattr(server,'pid',None),
                            'server_exit':server_exit,'display':display,
                            'socket_absent':not Path('/tmp/.X11-unix/X'+str(display)).exists(),
                            'repetition':repetition,'input_calls':0,'model_calls':0}
                write(out/'terminal.json',terminal)
    print(json.dumps(terminal))
    return 0 if not errors and len(rows)==12 and server_exit==0 and terminal['socket_absent'] else 1

if __name__ == '__main__':
    sys.exit(run(Path(sys.argv[1]),int(sys.argv[2])))
