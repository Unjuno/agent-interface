"""Live Xorg/Xvfb discriminator for delayed input after owner retirement.

This test is explicitly enabled only by the private-Xvfb integration job. It
must not send synthetic input to an arbitrary developer DISPLAY.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from Xlib import X, XK
from Xlib.display import Display
from Xlib.ext import xtest

from runtime.guarded_x11_v1.xres_client_fence import (
    client_is_connected,
    wait_for_client_disconnect_supervised,
)


_DELAY_MS = 8000
_POST_HORIZON_XRES_TIMEOUT_S = 10.0
_OWNER_START = r"""
import json, sys, time
from Xlib import X, XK
from Xlib.display import Display
from Xlib.ext import xtest

display_name, marker, delay_ms = sys.argv[1:]
d = Display(display_name)
keycodes = {name:d.keysym_to_keycode(XK.string_to_keysym(name))
            for name in ('a', 'b')}
base = d.display.info.resource_id_base
xtest.fake_input(d, X.KeyPress, detail=keycodes['a'], time=int(delay_ms))
xtest.fake_input(d, X.KeyPress, detail=keycodes['b'])
d.flush()
with open(marker, 'w', encoding='utf-8') as f:
    json.dump({'resource_base':base, 'keycodes':keycodes,
               'queued_ns':time.monotonic_ns()}, f)
d.sync()  # blocks until the delayed request is processed or the server closes it
"""
_IDLE_OWNER_START = r"""
import json, sys, time
from Xlib.display import Display

display_name, marker = sys.argv[1:]
d = Display(display_name)
with open(marker, 'w', encoding='utf-8') as f:
    json.dump({'resource_base':d.display.info.resource_id_base}, f)
while True:
    time.sleep(0.05)
"""


def _keys_down(display, keycodes):
    keymap = display.query_keymap()
    return {
        name:bool(keymap[code // 8] & (1 << (code % 8)))
        for name, code in keycodes.items()
    }


def _xvfb_build_provenance():
    """Capture the executable and package versions behind a private Xvfb run."""
    binary = shutil.which('Xvfb')
    resolved = str(Path(binary).resolve()) if binary else None
    digest = None
    if resolved and Path(resolved).is_file():
        sha = hashlib.sha256()
        with open(resolved, 'rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                sha.update(chunk)
        digest = sha.hexdigest()

    packages = {}
    for package in ('xvfb', 'xserver-xorg-core'):
        try:
            result = subprocess.run(
                ['dpkg-query', '-W', '-f=${binary:Package}=${Version}', package],
                capture_output=True, text=True, timeout=5, check=False)
            packages[package] = {
                'returncode':result.returncode,
                'stdout':result.stdout.strip(),
                'stderr':result.stderr.strip(),
            }
        except Exception as error:
            packages[package] = {'error':repr(error)}
    return {
        'path':binary,
        'resolved_path':resolved,
        'sha256':digest,
        'packages':packages,
    }


class XvfbBuildProvenanceTests(unittest.TestCase):
    def test_raw_provenance_binds_binary_hash_and_package_versions(self):
        with tempfile.TemporaryDirectory() as td:
            binary = Path(td)/'Xvfb'
            binary.write_bytes(b'controlled-xvfb-binary')
            package_results = [
                subprocess.CompletedProcess([], 0, 'xvfb=2:21.1.11-1', ''),
                subprocess.CompletedProcess([], 0, 'xserver-xorg-core=2:21.1.11-1', ''),
            ]
            with patch('runtime.guarded_x11_v1.test_xres_disconnect_fence_integration.shutil.which',
                       return_value=str(binary)), \
                    patch('runtime.guarded_x11_v1.test_xres_disconnect_fence_integration.subprocess.run',
                          side_effect=package_results):
                result = _xvfb_build_provenance()
            self.assertEqual(result['path'], str(binary))
            self.assertEqual(result['resolved_path'], str(binary.resolve()))
            self.assertEqual(result['sha256'], hashlib.sha256(
                b'controlled-xvfb-binary').hexdigest())
            self.assertEqual(result['packages']['xvfb']['stdout'],
                             'xvfb=2:21.1.11-1')
            self.assertEqual(result['packages']['xserver-xorg-core']['stdout'],
                             'xserver-xorg-core=2:21.1.11-1')


@unittest.skipUnless(
    sys.platform == 'linux'
    and os.environ.get('DISPLAY') == ':88'
    and os.environ.get('AGENT_INTERFACE_XORG_FENCE_TEST') == '1',
    'requires the explicitly enabled private Xorg/Xvfb display :88',
)
class XResDisconnectFenceIntegrationTests(unittest.TestCase):
    def _assert_owner_pid_absent(self, receipt, owner_pid, report):
        self.assertEqual(receipt['status'], 'disconnected', report)
        self.assertNotEqual(receipt['observed_pid'], owner_pid, report)
        if receipt['resource_base'] == receipt['observer_resource_base']:
            self.assertEqual(receipt['observed_pid'], receipt['observer_pid'], report)

    def test_dead_owner_delayed_xtest_outcome_after_fresh_cleanup(self):
        display_name = os.environ['DISPLAY']
        result_path = os.environ.get('AGENT_INTERFACE_XORG_FENCE_RESULT')
        report = {
            'server_display':display_name,
            'server_build_provenance':_xvfb_build_provenance(),
            'delayed_keypress_ms':_DELAY_MS,
            'kill_after_flush_ms':150,
            'server_vendor':None,
            'server_release_number':None,
            'xres_version':None,
            'xtest_version':None,
            'idle_control':None,
            'idle_control_disconnect_after_kill':None,
            'owner':None,
            'disconnect_before_delay_horizon':None,
            'disconnect_before_cleanup':None,
            'disconnect_after_delay_horizon':None,
            'key_down_after_extended_probe':None,
            'key_down_after_disconnect':None,
            'keycodes':None,
            'key_down_before':None,
            'key_down_before_delay_horizon':None,
            'key_down_before_cleanup':None,
            'key_down_after_cleanup':None,
            'key_down_after_delay_horizon':None,
            'cleanup_status':'not_attempted',
            'post_late_cleanup_status':'not_attempted',
        }
        owner = None
        idle_owner = None
        cleanup = None
        owner_returncode = None
        killed_ns = None
        marker_data = None
        keycodes = None
        observer = Display(display_name)
        try:
            info = observer.display.info
            report['server_vendor'] = str(info.vendor)
            report['server_release_number'] = info.release_number
            self.assertIn('X.Org', report['server_vendor'], report)
            self.assertTrue(observer.has_extension('X-Resource'), report)
            self.assertTrue(observer.has_extension('XTEST'), report)
            xres_version = observer.res_query_version()
            report['xres_version'] = [xres_version.server_major,
                                      xres_version.server_minor]
            xtest_version = xtest.get_version(observer, 2, 2)
            report['xtest_version'] = [xtest_version.major_version,
                                       xtest_version.minor_version]

            keycodes = {
                name:observer.keysym_to_keycode(XK.string_to_keysym(name))
                for name in ('a', 'b')
            }
            self.assertTrue(all(code > 0 for code in keycodes.values()), report)
            report['keycodes'] = keycodes
            for code in keycodes.values():
                xtest.fake_input(observer, X.KeyRelease, detail=code)
            observer.sync()
            report['key_down_before'] = _keys_down(observer, keycodes)
            self.assertFalse(any(report['key_down_before'].values()), report)

            with tempfile.TemporaryDirectory(prefix='xres-disconnect-fence-') as td:
                idle_marker = Path(td)/'idle-owner.json'
                idle_owner = subprocess.Popen(
                    [sys.executable, '-c', _IDLE_OWNER_START,
                     display_name, str(idle_marker)],
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                idle_marker_deadline = time.monotonic() + 3.0
                while (not idle_marker.exists()
                       and time.monotonic() < idle_marker_deadline):
                    if idle_owner.poll() is not None:
                        break
                    time.sleep(0.005)
                self.assertTrue(idle_marker.exists(), {
                    'idle_control_returncode':idle_owner.poll()})
                idle_data = json.loads(
                    idle_marker.read_text(encoding='utf-8'))
                report['idle_control'] = dict(idle_data, pid=idle_owner.pid)
                self.assertTrue(client_is_connected(
                    observer, idle_data['resource_base'],
                    expected_pid=idle_owner.pid), report)
                idle_owner.terminate()
                try:
                    idle_returncode = idle_owner.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    idle_owner.kill()
                    idle_returncode = idle_owner.wait(timeout=1.0)
                report['idle_control']['returncode'] = idle_returncode
                report['idle_control_disconnect_after_kill'] = (
                    wait_for_client_disconnect_supervised(
                        display_name, idle_data['resource_base'],
                        expected_pid=idle_owner.pid, timeout_s=2.0,
                        poll_interval_s=0.005, terminate_grace_s=0.1,
                    ))
                self._assert_owner_pid_absent(
                    report['idle_control_disconnect_after_kill'],
                    idle_owner.pid, report)
                report['idle_control_disappeared_within_2s'] = (
                    report['idle_control_disconnect_after_kill']['status']
                    == 'disconnected')

                marker = Path(td)/'owner.json'
                owner = subprocess.Popen(
                    [sys.executable, '-c', _OWNER_START, display_name,
                     str(marker), str(_DELAY_MS)],
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE, text=True,
                )
                marker_deadline = time.monotonic() + 3.0
                while not marker.exists() and time.monotonic() < marker_deadline:
                    if owner.poll() is not None:
                        break
                    time.sleep(0.005)
                self.assertTrue(marker.exists(), {
                    'owner_returncode':owner.poll(),
                    'stderr':owner.stderr.read() if owner.poll() is not None else None,
                })
                marker_data = json.loads(marker.read_text(encoding='utf-8'))
                report['owner'] = dict(marker_data, pid=owner.pid)
                self.assertEqual(marker_data['keycodes'], keycodes, report)
                self.assertTrue(client_is_connected(
                    observer, marker_data['resource_base'],
                    expected_pid=owner.pid), report)
                report['idle_resource_base_reused'] = (
                    idle_data['resource_base'] == marker_data['resource_base'])
                report['old_idle_pid_matches_current_base'] = client_is_connected(
                    observer, marker_data['resource_base'],
                    expected_pid=idle_owner.pid)
                self.assertFalse(report['old_idle_pid_matches_current_base'], report)

                time.sleep(report['kill_after_flush_ms']/1000)
                owner.terminate()
                killed_ns = time.monotonic_ns()
                report['queued_to_kill_ms'] = (
                    killed_ns-marker_data['queued_ns'])/1_000_000
                try:
                    owner_returncode = owner.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    owner.kill()
                    owner_returncode = owner.wait(timeout=1.0)
                report['owner']['returncode'] = owner_returncode
                report['owner_stderr'] = owner.stderr.read()
                self.assertNotEqual(owner_returncode, 0, report)

                early_disconnect = wait_for_client_disconnect_supervised(
                    display_name, marker_data['resource_base'],
                    expected_pid=owner.pid, timeout_s=1.0,
                    poll_interval_s=0.005, terminate_grace_s=0.1,
                )
                report['disconnect_before_delay_horizon'] = early_disconnect
                report['early_probe_after_kill_ms'] = (
                    time.monotonic_ns()-killed_ns)/1_000_000
                self._assert_owner_pid_absent(
                    early_disconnect, owner.pid, report)
                report['key_down_before_delay_horizon'] = _keys_down(
                    observer, keycodes)
                self.assertFalse(any(
                    report['key_down_before_delay_horizon'].values()), report)

                before_cleanup = wait_for_client_disconnect_supervised(
                    display_name, marker_data['resource_base'],
                    expected_pid=owner.pid, timeout_s=5.0,
                    poll_interval_s=0.005, terminate_grace_s=0.1,
                )
                report['disconnect_before_cleanup'] = before_cleanup
                self._assert_owner_pid_absent(before_cleanup, owner.pid, report)
                report['before_cleanup_after_kill_ms'] = (
                    time.monotonic_ns()-killed_ns)/1_000_000
                report['key_down_before_cleanup'] = _keys_down(
                    observer, keycodes)
                self.assertFalse(any(
                    report['key_down_before_cleanup'].values()), report)

                # Independently release while the delayed owner request is
                # still scheduled. A later DOWN is the discriminator, not an
                # assumed XRes disappearance time.
                cleanup = Display(display_name)
                for code in keycodes.values():
                    xtest.fake_input(cleanup, X.KeyRelease, detail=code)
                cleanup.sync()
                report['cleanup_status'] = 'key_release_sync_completed'
                report['key_down_after_cleanup'] = _keys_down(cleanup, keycodes)
                self.assertFalse(any(report['key_down_after_cleanup'].values()), report)

                # Observe beyond the owner's scheduled event time. The
                # independent cleanup is already read back as key-up here.
                horizon_ns = killed_ns + (_DELAY_MS+500)*1_000_000
                while time.monotonic_ns() < horizon_ns:
                    time.sleep(min(0.02,
                        (horizon_ns-time.monotonic_ns())/1_000_000_000))
                report['delay_event_horizon_after_kill_ms'] = (
                    time.monotonic_ns()-killed_ns)/1_000_000
                report['key_down_after_delay_horizon'] = _keys_down(
                    cleanup, keycodes)
                report['late_input_observed'] = any(
                    report['key_down_after_delay_horizon'].values())
                report['post_horizon_xres_timeout_s'] = (
                    _POST_HORIZON_XRES_TIMEOUT_S)
                report['disconnect_after_delay_horizon'] = (
                    wait_for_client_disconnect_supervised(
                        display_name, marker_data['resource_base'],
                        expected_pid=owner.pid,
                        timeout_s=_POST_HORIZON_XRES_TIMEOUT_S,
                        poll_interval_s=0.005, terminate_grace_s=0.1,
                    ))
                self._assert_owner_pid_absent(
                    report['disconnect_after_delay_horizon'], owner.pid, report)
                report['post_horizon_xres_probe_after_kill_ms'] = (
                    time.monotonic_ns()-killed_ns)/1_000_000
                report['key_down_after_extended_probe'] = _keys_down(
                    cleanup, keycodes)
                if report['disconnect_after_delay_horizon']['status'] == 'disconnected':
                    report['key_down_after_disconnect'] = dict(
                        report['key_down_after_extended_probe'])
                report['late_input_observed_after_extended_probe'] = any(
                    report['key_down_after_extended_probe'].values())
                # This is an observational discriminator: either key state is
                # a valid measured outcome. The report, not an assumed late
                # press, carries the result. Fail only if the readback itself
                # was not produced or does not cover the requested keys.
                self.assertEqual(
                    set(report['key_down_after_delay_horizon']),
                    set(keycodes), report)
                self.assertEqual(
                    set(report['key_down_after_extended_probe']),
                    set(keycodes), report)

                for code in keycodes.values():
                    xtest.fake_input(cleanup, X.KeyRelease, detail=code)
                cleanup.sync()
                report['post_late_cleanup_status'] = 'key_release_sync_completed'
                report['final_key_down'] = _keys_down(cleanup, keycodes)
                self.assertFalse(any(report['final_key_down'].values()), report)
        finally:
            if idle_owner is not None and idle_owner.poll() is None:
                idle_owner.kill()
                idle_owner.wait(timeout=1.0)
            if owner is not None and owner.poll() is None:
                if killed_ns is None:
                    killed_ns = time.monotonic_ns()
                owner.kill()
                owner_returncode = owner.wait(timeout=1.0)
            if owner is not None and owner.stderr and not owner.stderr.closed:
                report['owner_stderr'] = owner.stderr.read()
            if (marker_data is not None and killed_ns is not None
                    and cleanup is None):
                try:
                    wait_for_client_disconnect_supervised(
                        display_name, marker_data['resource_base'],
                        expected_pid=owner.pid, timeout_s=1.0,
                        poll_interval_s=0.005, terminate_grace_s=0.1,
                    )
                except Exception:
                    pass
            if keycodes is not None and killed_ns is not None:
                horizon_ns = killed_ns + (_DELAY_MS+500)*1_000_000
                while time.monotonic_ns() < horizon_ns:
                    time.sleep(min(0.02,
                        (horizon_ns-time.monotonic_ns())/1_000_000_000))
            if cleanup is None and observer is not None:
                cleanup = observer
                observer = None
            if cleanup is not None and keycodes is not None:
                try:
                    for code in keycodes.values():
                        xtest.fake_input(cleanup, X.KeyRelease, detail=code)
                    cleanup.sync()
                    report['final_cleanup_status'] = 'key_release_sync_completed'
                    report['final_key_down'] = _keys_down(cleanup, keycodes)
                except Exception as error:
                    report['final_cleanup_status'] = 'key_release_sync_failed'
                    report['cleanup_error'] = repr(error)
            report['owner_returncode'] = owner_returncode
            if cleanup is not None:
                cleanup.close()
            if observer is not None:
                observer.close()
            if result_path:
                Path(result_path).write_text(
                    json.dumps(report, indent=2, sort_keys=True)+'\n',
                    encoding='utf-8',
                )


if __name__ == '__main__':
    unittest.main()
