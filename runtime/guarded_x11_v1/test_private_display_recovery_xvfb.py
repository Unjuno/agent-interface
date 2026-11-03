"""Private Xvfb regression for recovery owner binding."""
import importlib.util
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

@unittest.skipUnless(sys.platform.startswith('linux') and hasattr(os, 'pidfd_open')
                     and shutil.which('Xvfb') and shutil.which('xauth')
                     and importlib.util.find_spec('Xlib'), 'Linux pidfd, Xvfb, xauth and Xlib required')
class RecoveryBindingXvfbTests(unittest.TestCase):
    def test_real_pinned_owner_with_no_active_call_stays_unknown(self):
        from Xlib import X, display
        from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
        from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
        from runtime.guarded_x11_v1.private_display_recovery import PrivateDisplayRecovery
        with tempfile.TemporaryDirectory() as tmp:
            owner = PrivateDisplayOwner(Path(tmp) / 'display')
            guard = app = None
            try:
                session = owner.start(timeout_s=5)
                with patch.dict(os.environ, {'XAUTHORITY':str(session.authority)}):
                    app = display.Display(session.display)
                win = app.screen().root.create_window(10,10,100,80,0,
                    app.screen().root_depth,X.InputOutput,X.CopyFromParent)
                win.map(); app.sync()
                guard = OwnedGuardedSessionOwner({'app':win.id}, Path(tmp)/'guard', session.display,
                    process_identity=True,query_worker=True,prestarted_cancel_supervisor=True,
                    xauthority=str(session.authority),_owned_display_owner=owner)
                guard._ensure_started()
                recovery = PrivateDisplayRecovery(owner,guard)
                result = recovery.cancel_guarded('not-an-active-token',deadline_monotonic_ns=time.monotonic_ns()+3_000_000_000)
                self.assertEqual(result['status'],'unknown',result)
                self.assertFalse(result['fresh_display_allowed'],result)
                self.assertFalse(result['release_confirmed'],result)
                self.assertIsNone(owner._process.poll())
            finally:
                try:
                    if guard is not None: guard.close()
                finally:
                    try:
                        if app is not None: app.close()
                    finally:
                        owner.close()

    def test_other_owned_server_survives_misbound_recovery(self):
        from Xlib import X, display
        from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
        from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
        from runtime.guarded_x11_v1.private_display_recovery import PrivateDisplayRecovery
        with tempfile.TemporaryDirectory() as tmp:
            a = PrivateDisplayOwner(Path(tmp) / 'a')
            b = PrivateDisplayOwner(Path(tmp) / 'b')
            guard = app = None
            try:
                sa = a.start(timeout_s=5); sb = b.start(timeout_s=5)
                with patch.dict(os.environ, {'XAUTHORITY':str(sa.authority)}):
                    app = display.Display(sa.display)
                win = app.screen().root.create_window(10,10,100,80,0,
                    app.screen().root_depth,X.InputOutput,X.CopyFromParent)
                win.map(); app.sync()
                guard = OwnedGuardedSessionOwner({'app':win.id}, Path(tmp)/'owner', sa.display,
                    process_identity=True,query_worker=True,prestarted_cancel_supervisor=True,
                    xauthority=str(sa.authority),_owned_display_owner=a)
                guard._ensure_started()
                self.assertEqual(guard.state,'open')
                # Simulate stale name/authority metadata, while the real owner remains pinned to A.
                guard.display_name = sb.display; guard._xauthority = str(sb.authority)
                result = None; rejected = False
                with patch.object(guard,'cancel_guarded',return_value={
                    'status':'cancel_unconfirmed','cleanup_status':'UNKNOWN',
                    'owner_process_retired':True,'release_confirmed':False,'replay_allowed':False}):
                    try: recovery = PrivateDisplayRecovery(b,guard)
                    except ValueError: rejected = True
                    else: result = recovery.cancel_guarded('token',deadline_monotonic_ns=time.monotonic_ns()+3_000_000_000)
                self.assertTrue(rejected, f'wrong binding was accepted: {result!r}; B exit={b._process.poll()!r}')
                self.assertIsNone(b._process.poll(), 'unrelated owned server B was retired')
                self.assertIsNone(a._process.poll(), 'server A unexpectedly exited')
            finally:
                try:
                    if guard is not None:
                        guard.display_name=sa.display; guard._xauthority=str(sa.authority)
                        guard.close()
                finally:
                    try:
                        if app is not None: app.close()
                    finally:
                        try: b.close()
                        finally: a.close()

if __name__ == '__main__': unittest.main()
