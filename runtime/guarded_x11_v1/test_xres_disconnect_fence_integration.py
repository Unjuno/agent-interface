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


_DELAY_MS = 3000
_OWNER_START = r"""
import json, sys, time
from Xlib import X, XK
from Xlib.display import Display
from Xlib.ext import xtest

display_name, marker = sys.argv[1:]
d = Display(display_name)
keycode = d.keysym_to_keycode(XK.string_to_keysym('a'))
base = d.display.info.resource_id_base
xtest.fake_input(d, X.KeyPress, detail=keycode, time=3000)
d.flush()
with open(marker, 'w', encoding='utf-8') as f:
    json.dump({'resource_base':base, 'keycode':keycode,
               'queued_ns':time.monotonic_ns()}, f)
d.sync()  # blocks until the delayed request is processed or the server closes it
"""


def _key_down(display, keycode):
    keymap = display.query_keymap()
    return bool(keymap[keycode // 8] & (1 << (keycode % 8)))


@unittest.skipUnless(
    sys.platform == 'linux'
    and os.environ.get('DISPLAY') == ':88'
    and os.environ.get('AGENT_INTERFACE_XORG_FENCE_TEST') == '1',
    'requires the explicitly enabled private Xorg/Xvfb display :88',
)
class XResDisconnectFenceIntegrationTests(unittest.TestCase):
    def test_retired_owner_cannot_emit_delayed_keypress_after_xres_disconnect(self):
        display_name = os.environ['DISPLAY']
        result_path = os.environ.get('AGENT_INTERFACE_XORG_FENCE_RESULT')
        report = {
            'server_display':display_name,
            'delayed_keypress_ms':_DELAY_MS,
            'kill_after_flush_ms':150,
            'server_vendor':None,
            'server_release':None,
            'xres_version':None,
            'xtest_version':None,
            'owner':None,
            'disconnect':None,
            'key_down_before':None,
            'key_down_after_disconnect':None,
            'key_down_after_cleanup':None,
            'key_down_after_delay_horizon':None,
            'cleanup_status':'not_attempted',
        }
        owner = None
        cleanup = None
        owner_returncode = None
        killed_ns = None
        marker_data = None
        keycode = None
        observer = Display(display_name)
        try:
            info = observer.display.info
            report['server_vendor'] = str(info.vendor)
            report['server_release'] = info.release
            self.assertIn('X.Org', report['server_vendor'], report)
            self.assertTrue(observer.has_extension('X-Resource'), report)
            self.assertTrue(observer.has_extension('XTEST'), report)
            xres_version = observer.res_query_version()
            report['xres_version'] = [xres_version.server_major,
                                      xres_version.server_minor]
            xtest_version = xtest.get_version(observer, 2, 2)
            report['xtest_version'] = [xtest_version.major_version,
                                       xtest_version.minor_version]

            keycode = observer.keysym_to_keycode(XK.string_to_keysym('a'))
            self.assertGreater(keycode, 0, report)
            xtest.fake_input(observer, X.KeyRelease, detail=keycode)
            observer.sync()
            report['key_down_before'] = _key_down(observer, keycode)
            self.assertFalse(report['key_down_before'], report)

            with tempfile.TemporaryDirectory(prefix='xres-disconnect-fence-') as td:
                marker = Path(td)/'owner.json'
                owner = subprocess.Popen(
                    [sys.executable, '-c', _OWNER_START, display_name, str(marker)],
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
                self.assertEqual(marker_data['keycode'], keycode, report)
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

                disconnect = wait_for_client_disconnect_supervised(
                    display_name, marker_data['resource_base'], timeout_s=2.0,
                    poll_interval_s=0.005, terminate_grace_s=0.1,
                )
                report['disconnect'] = disconnect
                report['disconnect_after_kill_ms'] = (
                    time.monotonic_ns()-killed_ns)/1_000_000
                self.assertEqual(disconnect['status'], 'disconnected', report)
                self.assertLess(report['disconnect_after_kill_ms'], 1500, report)
                report['key_down_after_disconnect'] = _key_down(observer, keycode)
                self.assertFalse(report['key_down_after_disconnect'], report)

                cleanup = Display(display_name)
                xtest.fake_input(cleanup, X.KeyRelease, detail=keycode)
                cleanup.sync()
                report['cleanup_status'] = 'key_release_sync_completed'
                report['key_down_after_cleanup'] = _key_down(cleanup, keycode)
                self.assertFalse(report['key_down_after_cleanup'], report)

                # Keep observing beyond the request's scheduled event time. A
                # late DOWN after the cleanup readback fails this discriminator.
                horizon_ns = (time.monotonic_ns()
                              + (_DELAY_MS+500)*1_000_000)
                while time.monotonic_ns() < horizon_ns:
                    time.sleep(min(0.02,
                        (horizon_ns-time.monotonic_ns())/1_000_000_000))
                report['key_down_after_delay_horizon'] = _key_down(cleanup, keycode)
                self.assertFalse(report['key_down_after_delay_horizon'], report)
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
            if keycode is not None and killed_ns is not None:
                horizon_ns = killed_ns + (_DELAY_MS+500)*1_000_000
                while time.monotonic_ns() < horizon_ns:
                    time.sleep(min(0.02,
                        (horizon_ns-time.monotonic_ns())/1_000_000_000))
            if cleanup is None and observer is not None:
                cleanup = observer
                observer = None
            if cleanup is not None and keycode is not None:
                try:
                    xtest.fake_input(cleanup, X.KeyRelease,
                                     detail=keycode)
                    cleanup.sync()
                    report['final_cleanup_status'] = 'key_release_sync_completed'
                    report['final_key_down'] = _key_down(
                        cleanup, keycode)
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
