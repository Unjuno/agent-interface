"""Live Xorg/Xvfb discriminator for delayed input after owner retirement.

This test is explicitly enabled only by the private-Xvfb integration job. It
must not send synthetic input to an arbitrary developer DISPLAY.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from Xlib import X, XK
from Xlib.display import Display
from Xlib.ext import xtest

from runtime.guarded_x11_v1.xres_client_fence import (
    client_is_connected,
    wait_for_client_disconnect_supervised,
)


_DELAY_MS = 8000
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


def _keys_down(display, keycodes):
    keymap = display.query_keymap()
    return {
        name:bool(keymap[code // 8] & (1 << (code % 8)))
        for name, code in keycodes.items()
    }


@unittest.skipUnless(
    sys.platform == 'linux'
    and os.environ.get('DISPLAY') == ':88'
    and os.environ.get('AGENT_INTERFACE_XORG_FENCE_TEST') == '1',
    'requires the explicitly enabled private Xorg/Xvfb display :88',
)
class XResDisconnectFenceIntegrationTests(unittest.TestCase):
    def test_dead_owner_delayed_xtest_can_press_after_fresh_cleanup(self):
        display_name = os.environ['DISPLAY']
        result_path = os.environ.get('AGENT_INTERFACE_XORG_FENCE_RESULT')
        report = {
            'server_display':display_name,
            'delayed_keypress_ms':_DELAY_MS,
            'kill_after_flush_ms':150,
            'server_vendor':None,
            'server_release_number':None,
            'xres_version':None,
            'xtest_version':None,
            'owner':None,
            'disconnect_before_delay_horizon':None,
            'disconnect_before_cleanup':None,
            'disconnect_after_delay_horizon':None,
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
                    observer, marker_data['resource_base']), report)

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
                    display_name, marker_data['resource_base'], timeout_s=1.0,
                    poll_interval_s=0.005, terminate_grace_s=0.1,
                )
                report['disconnect_before_delay_horizon'] = early_disconnect
                report['early_probe_after_kill_ms'] = (
                    time.monotonic_ns()-killed_ns)/1_000_000
                self.assertEqual(early_disconnect['status'], 'still_connected', report)
                report['key_down_before_delay_horizon'] = _keys_down(
                    observer, keycodes)
                self.assertFalse(any(
                    report['key_down_before_delay_horizon'].values()), report)

                before_cleanup = wait_for_client_disconnect_supervised(
                    display_name, marker_data['resource_base'], timeout_s=5.0,
                    poll_interval_s=0.005, terminate_grace_s=0.1,
                )
                report['disconnect_before_cleanup'] = before_cleanup
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
                report['disconnect_after_delay_horizon'] = (
                    wait_for_client_disconnect_supervised(
                        display_name, marker_data['resource_base'], timeout_s=1.0,
                        poll_interval_s=0.005, terminate_grace_s=0.1,
                    ))
                self.assertTrue(
                    report['key_down_after_delay_horizon']['a'], report)

                for code in keycodes.values():
                    xtest.fake_input(cleanup, X.KeyRelease, detail=code)
                cleanup.sync()
                report['post_late_cleanup_status'] = 'key_release_sync_completed'
                report['final_key_down'] = _keys_down(cleanup, keycodes)
                self.assertFalse(any(report['final_key_down'].values()), report)
        finally:
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
                        display_name, marker_data['resource_base'], timeout_s=1.0,
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
