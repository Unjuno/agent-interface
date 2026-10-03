"""Launch only owned private X11 processes for construction test execution."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def run():
    with tempfile.TemporaryDirectory(prefix='a15-construction-') as directory:
        root = Path(directory)
        cache = root/'font-cache'
        cache.mkdir()
        child_environment = dict(os.environ, DISPLAY=':97', XDG_CACHE_HOME=str(cache))
        processes = []
        streams = []
        try:
            for name, argv in [('xvfb', ['Xvfb', ':97', '-screen', '0', '640x480x24',
                                        '-nolisten', 'tcp', '-ac']),
                               ('openbox', ['openbox', '--sm-disable'])]:
                stream = (root/(name+'.log')).open('wb')
                streams.append(stream)
                processes.append(subprocess.Popen(argv, stdout=stream, stderr=stream,
                                                   env=child_environment))
                from Xlib import display
                deadline = time.monotonic()+5
                while True:
                    connection = None
                    try:
                        connection = display.Display(':97')
                        if name == 'openbox':
                            atom = connection.intern_atom('_NET_SUPPORTING_WM_CHECK')
                            if connection.screen().root.get_full_property(atom, 0) is None:
                                raise RuntimeError('WM not ready')
                        break
                    except Exception:
                        if processes[-1].poll() is not None or time.monotonic() >= deadline:
                            raise RuntimeError(name+' private construction readiness failed')
                        time.sleep(0.01)
                    finally:
                        if connection is not None:
                            connection.close()
            if sys.argv[1:2] == ['--study']:
                command = [sys.executable, '-B', str(Path(__file__).parent/'paired_study.py'),
                           *sys.argv[2:]]
            else:
                command = [sys.executable, '-B', '-m', 'unittest', *sys.argv[1:]]
            return subprocess.call(command, env=child_environment)
        finally:
            for process in reversed(processes):
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=3)
            for stream in streams:
                stream.close()


if __name__ == '__main__':
    raise SystemExit(run())
