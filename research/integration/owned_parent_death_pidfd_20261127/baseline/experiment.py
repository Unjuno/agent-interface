import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
from runtime.cli_v1.test_mcp_owned_process import _fake_owner_factory

root = Path('/home/user/owned-parent-death-20261127-r01')

def gated_factory(targets, directory, display_name, options):
    (root / 'child-pid').write_text(str(os.getpid()))
    (root / 'factory-entered').write_text('entered')
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
    report = {'scope': 'isolated PID namespace; synthetic owner; forced parent death',
              'factory_resumed_after_parent_death': None}
    child_fd = None
    parent = subprocess.Popen([sys.executable, __file__, 'parent'])
    try:
        report['parent_pid'] = parent.pid
        report['factory_entered'] = wait_for(root / 'factory-entered')
        if not report['factory_entered']: raise RuntimeError('factory did not enter')
        child_pid = int((root / 'child-pid').read_text())
        child_fd = os.pidfd_open(child_pid)
        report['child_pid'] = child_pid
        report['child_alive_before_parent_kill'] = not bool(select.select([child_fd], [], [], 0)[0])
        parent.kill()
        report['parent_exit_code'] = parent.wait(timeout=5)
        (root / 'resume').write_text('resume after parent exit')
        report['factory_resumed_after_parent_death'] = wait_for(root / 'factory-resumed', 5)
    finally:
        if parent.poll() is None:
            parent.kill(); parent.wait(timeout=5)
        if child_fd is not None:
            if not select.select([child_fd], [], [], 0)[0]:
                signal.pidfd_send_signal(child_fd, signal.SIGKILL)
            report['child_exit_observed'] = bool(select.select([child_fd], [], [], 5)[0])
            os.close(child_fd)
        print(json.dumps(report, indent=2))
    if not report.get('child_exit_observed'):
        raise SystemExit(1)
