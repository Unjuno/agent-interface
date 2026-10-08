"""Private disposable Xvfb/Openbox session; never touches the ambient display."""
from contextlib import contextmanager
import os
from pathlib import Path
import select
import subprocess
import tempfile
import time

@contextmanager
def desktop(log_dir):
    with tempfile.TemporaryDirectory(prefix='ai-release-effect-') as tmp:
        env = dict(os.environ, HOME=tmp, XDG_CONFIG_HOME=tmp + '/config', XDG_CACHE_HOME=tmp + '/cache', XDG_RUNTIME_DIR=tmp + '/runtime')
        for key in ('XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'XDG_RUNTIME_DIR'):
            Path(env[key]).mkdir(mode=448)
        read_fd, write_fd = os.pipe()
        logs = []
        procs = []
        try:
            log = (log_dir / 'xvfb.log').open('w')
            logs.append(log)
            proc = subprocess.Popen(['Xvfb', '-displayfd', str(write_fd), '-screen', '0', '1024x768x24', '-nolisten', 'tcp', '-ac'], pass_fds=(write_fd,), stdout=log, stderr=subprocess.STDOUT)
            procs.append(proc)
            os.close(write_fd)
            write_fd = -1
            if not select.select([read_fd], [], [], 5)[0]:
                raise TimeoutError('private Xvfb did not become ready')
            env['DISPLAY'] = ':' + os.read(read_fd, 64).decode().strip()
            if env['DISPLAY'] == ':':
                raise RuntimeError('private Xvfb failed')
            env.pop('WAYLAND_DISPLAY', None)
            env['XAUTHORITY'] = tmp + '/authority'
            Path(env['XAUTHORITY']).touch()
            log = (log_dir / 'openbox.log').open('w')
            logs.append(log)
            procs.append(subprocess.Popen(['openbox'], env=env, stdout=log, stderr=subprocess.STDOUT))
            time.sleep(0.3)
            original_auth = os.environ.get('XAUTHORITY')
            os.environ['XAUTHORITY'] = env['XAUTHORITY']
            try:
                yield env
            finally:
                if original_auth is None:
                    os.environ.pop('XAUTHORITY', None)
                else:
                    os.environ['XAUTHORITY'] = original_auth
        finally:
            os.close(read_fd)
            if write_fd >= 0:
                os.close(write_fd)
            for proc in reversed(procs):
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            for log in logs:
                log.close()
