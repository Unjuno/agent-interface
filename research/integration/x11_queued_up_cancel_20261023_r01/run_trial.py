"""Single native-WSL2, private-Xvfb schedule; no WSLc or desktop input."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import tempfile
import time
import traceback

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[2]
HERE = SOURCE / sys.argv[sys.argv.index('--case')+1]


def save(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=2) + '\n', encoding='utf-8')


def verify_sources():
    for name, expected in json.loads((SOURCE / 'SOURCES.json').read_text()).items():
        value = hashlib.sha256((ROOT / name).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
        if value != expected:
            raise ValueError('source mismatch: ' + name)


def child():
    # Retain the integration test's outer scratch directory at its original path.
    # Other temporary-directory cleanup keeps its normal semantics.
    import unittest
    original = tempfile.TemporaryDirectory
    class RetainedOuterDirectory(original):
        def cleanup(self):
            if Path(self.name).name.startswith('mcp-xvfb-blocked-release-'):
                self._finalizer.detach()
                return
            super().cleanup()
    tempfile.TemporaryDirectory = RetainedOuterDirectory
    sys.path.insert(0, str(ROOT))
    suite = unittest.defaultTestLoader.loadTestsFromName(
        'runtime.cli_v1.test_mcp_xvfb_blocked_release_integration')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    save('unittest-summary.json', {'tests_run': result.testsRun,
        'skipped': len(result.skipped), 'failures': len(result.failures),
        'errors': len(result.errors), 'successful': result.wasSuccessful()})
    return 0 if result.wasSuccessful() and result.testsRun == 1 and not result.skipped else 1


def main():
    verify_sources()
    conditions = json.loads((HERE / 'conditions.json').read_text())
    if hashlib.sha256(Path('/usr/bin/Xvfb').read_bytes()).hexdigest() != conditions['xvfb_sha256']:
        raise ValueError('Xvfb binary changed')
    for name in ('/tmp/.X88-lock', '/tmp/.X11-unix/X88'):
        if Path(name).exists():
            raise RuntimeError('display already occupied: ' + name)
    with (HERE / 'attempt-started.json').open('x') as stream:
        json.dump({'run_id': conditions['run_id'], 'monotonic_ns': time.monotonic_ns(),
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}, stream)
    report = {'status': 'FAIL', 'test_exit_code': None, 'cleanup': {},
        'started_ns': time.monotonic_ns()}
    server = test = None
    server_fd = None
    try:
        with tempfile.TemporaryDirectory(prefix='ai-control-auth-') as td:
            auth = Path(td) / 'Xauthority'
            auth.touch(mode=0o600)
            subprocess.run(['/usr/bin/xauth', '-f', str(auth), 'add', ':88', '.',
                secrets.token_hex(16)], capture_output=True, check=True, timeout=5)
            env = dict(os.environ, DISPLAY=':88', XAUTHORITY=str(auth),
                PYTHONDONTWRITEBYTECODE='1', TMPDIR=str(HERE / 'raw'),
                AGENT_INTERFACE_MCP_XVFB_TEST='1',
                AGENT_INTERFACE_MCP_XVFB_CANCEL_ACK_WITHHOLD_S='0',
                AGENT_INTERFACE_MCP_XVFB_TRACE_OWNER_PROCESS_METHODS='1',
                AGENT_INTERFACE_MCP_XVFB_PRESTARTED_CANCEL_SUPERVISOR='1',
                AGENT_INTERFACE_MCP_XVFB_SERVER_PAUSE_MS=str(conditions['pause_ms']),
                AGENT_INTERFACE_MCP_XVFB_BLOCKED_RELEASE_RESULT=str(HERE / 'result.json'),
                GITHUB_SHA=conditions['source_commit'], OPENBLAS_NUM_THREADS='1',
                OMP_NUM_THREADS='1')
            env.pop('WAYLAND_DISPLAY', None)
            (HERE / 'raw').mkdir(exist_ok=False)
            # One finite job on two inherited CPUs; no system-wide affinity change.
            cpus = sorted(os.sched_getaffinity(0))[:2]
            os.sched_setaffinity(0, cpus)
            os.nice(10)
            report['cpu_affinity'] = cpus
            with (HERE / 'xvfb.txt').open('wb') as log:
                server = subprocess.Popen(['/usr/bin/Xvfb', ':88', '-screen', '0',
                    '1024x768x24', '-nolisten', 'tcp', '-auth', str(auth)],
                    stdout=log, stderr=subprocess.STDOUT, env=env)
                server_fd = os.pidfd_open(server.pid)
                report['xvfb_pid'] = server.pid
                report['xvfb_pidfd'] = Path('/proc/self/fdinfo/' + str(server_fd)).read_text()
                report['xvfb_stat'] = Path('/proc/' + str(server.pid) + '/stat').read_text()
                env['AGENT_INTERFACE_XVFB_PID'] = str(server.pid)
                time.sleep(0.5)
                if server.poll() is not None:
                    raise RuntimeError('Xvfb exited before test entry')
                # Authenticated connection is the readiness check, not pathname existence.
                from Xlib import display
                old_auth = os.environ.get('XAUTHORITY')
                os.environ['XAUTHORITY'] = str(auth)
                try:
                    connection = display.Display(':88')
                    report['readiness_vendor'] = connection.display.info.vendor
                    connection.close()
                finally:
                    if old_auth is None:
                        os.environ.pop('XAUTHORITY', None)
                    else:
                        os.environ['XAUTHORITY'] = old_auth
                command = [sys.executable, '-B', str(Path(__file__).resolve()), '--test', '--case', HERE.name]
                test = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    cwd=ROOT, env=env, start_new_session=True)
                report['test_pid'] = test.pid
                report['test_command'] = command
                report['test_stat'] = Path('/proc/' + str(test.pid) + '/stat').read_text()
                save('process-started.json', report)
                try:
                    stdout, stderr = test.communicate(timeout=210)
                except subprocess.TimeoutExpired:
                    # Still-unreaped session leader pins this process-group identity.
                    signal.pidfd_send_signal(server_fd, signal.SIGCONT)
                    os.killpg(test.pid, signal.SIGTERM)
                    try:
                        stdout, stderr = test.communicate(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(test.pid, signal.SIGKILL)
                        stdout, stderr = test.communicate(timeout=5)
                    report['test_timed_out'] = True
                (HERE / 'test-stdout.txt').write_bytes(stdout)
                (HERE / 'test-stderr.txt').write_bytes(stderr)
                report['test_exit_code'] = test.returncode
                verify_sources()
                report['postrun_sources_match'] = True
                summary = json.loads((HERE / 'unittest-summary.json').read_text())
                if test.returncode == 0 and summary['tests_run'] == 1 and summary['skipped'] == 0:
                    report['status'] = 'OBSERVED_TEST_PASS_PENDING_RAW_AUDIT'
    except BaseException as error:
        report['error'] = repr(error)
        report['traceback'] = traceback.format_exc()
    finally:
        if server_fd is not None:
            try:
                signal.pidfd_send_signal(server_fd, signal.SIGCONT)
                signal.pidfd_send_signal(server_fd, signal.SIGTERM)
                report['cleanup']['xvfb_exit_code'] = server.wait(timeout=5)
            except BaseException as error:
                report['cleanup']['error'] = repr(error)
                report['status'] = 'FAIL_CLEANUP'
                try:
                    signal.pidfd_send_signal(server_fd, signal.SIGKILL)
                    report['cleanup']['xvfb_kill_exit_code'] = server.wait(timeout=5)
                except BaseException as error2:
                    report['cleanup']['kill_error'] = repr(error2)
            os.close(server_fd)
        elif server is not None:
            server.terminate()
            report['cleanup']['unpinned_child_exit_code'] = server.wait(timeout=5)
        report['ended_ns'] = time.monotonic_ns()
        save('launcher-result.json', report)
    print(json.dumps({'status': report['status'], 'test_exit_code': report['test_exit_code'],
        'error': report.get('error')}))
    return 0 if report['status'] == 'OBSERVED_TEST_PASS_PENDING_RAW_AUDIT' else 1


if __name__ == '__main__':
    raise SystemExit(child() if '--test' in sys.argv else main())
