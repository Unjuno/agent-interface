import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import threading
import time

from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
from runtime.cli_v1.test_mcp_owned_process import _fake_owner_factory

root = Path('/home/user/owned-parent-pidfd-watch-20261127-r01')

def gated_factory(targets, directory, display_name, options):
    parent_fd = os.pidfd_open(os.getppid())
    def watch_parent():
        select.select([parent_fd], [], [])
        (root / 'parent-death-observed').write_text('observed')
        os._exit(91)
    threading.Thread(target=watch_parent, daemon=True).start()
    (root / 'child-pid').write_text(str(os.getpid()))
    (root / 'watcher-armed').write_text('armed')
    deadline = time.monotonic() + 25
    while not (root / 'resume').exists():
        if time.monotonic() >= deadline: raise TimeoutError('factory gate')
        time.sleep(.01)
    (root / 'factory-resumed').write_text('resumed')
    return _fake_owner_factory(targets, directory, display_name, options)

def wait_for(path, timeout=8):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if path.exists(): return True
        time.sleep(.01)
    return path.exists()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'parent':
        owner = OwnedGuardedSessionOwner({'app': 20}, root / 'owner', _owner_factory=gated_factory)
        owner._ensure_started()
        raise SystemExit(0)
    report = {'scope': 'isolated PID namespace; synthetic owner; child-side pidfd watcher',
              'watcher_armed': False}
    child_fd = None
    parent = subprocess.Popen([sys.executable, __file__, 'parent'])
    try:
        report['parent_pid'] = parent.pid
        report['watcher_armed'] = wait_for(root / 'watcher-armed')
        if not report['watcher_armed']: raise RuntimeError('watcher did not arm')
        child_pid = int((root / 'child-pid').read_text())
        child_fd = os.pidfd_open(child_pid)
        report['child_pid'] = child_pid
        report['child_alive_before_parent_kill'] = not bool(select.select([child_fd], [], [], 0)[0])
        parent.kill()
        report['parent_exit_code'] = parent.wait(timeout=5)
        report['child_exited_before_fixture_signal'] = bool(select.select([child_fd], [], [], 5)[0])
        (root / 'resume').write_text('resume after parent exit')
        report['parent_death_marker'] = (root / 'parent-death-observed').exists()
        report['factory_resumed'] = (root / 'factory-resumed').exists()
        report['pass'] = (report['child_alive_before_parent_kill']
                          and report['parent_exit_code'] == -9
                          and report['child_exited_before_fixture_signal']
                          and report['parent_death_marker'] and not report['factory_resumed'])
    finally:
        if parent.poll() is None:
            parent.kill(); parent.wait(timeout=5)
        if child_fd is not None:
            if not select.select([child_fd], [], [], 0)[0]:
                signal.pidfd_send_signal(child_fd, signal.SIGKILL)
            report['child_exit_observed'] = bool(select.select([child_fd], [], [], 5)[0])
            os.close(child_fd)
        print(json.dumps(report, indent=2))
    if not report.get('pass') or not report.get('child_exit_observed'):
        raise SystemExit(1)
