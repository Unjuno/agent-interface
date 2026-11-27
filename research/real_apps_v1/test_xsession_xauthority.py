"""Integration coverage for the private Xvfb session authentication boundary."""
import io
import os
import shutil
import unittest
from contextlib import redirect_stdout

from research.observation_gating.gui_suite import Session
from runtime.guarded_x11_v1.target_queries import X11TargetQueries


@unittest.skipUnless(all(shutil.which(name) for name in ("Xvfb", "openbox", "xauth")),
                     "requires Xvfb, Openbox, and xauth")
class XSessionXAuthorityTests(unittest.TestCase):
    def test_private_display_clients_do_not_print_xauth_warning_to_protocol_stdout(self):
        captured_stdout = io.StringIO()
        env_before = {name: os.environ.get(name)
                      for name in ("DISPLAY", "XAUTHORITY")}
        session = None
        try:
            with redirect_stdout(captured_stdout):
                session = Session()
                query = X11TargetQueries(session.name)
                query.close()
        finally:
            if session is not None:
                session.close()
            for name, value in env_before.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value

        self.assertEqual(captured_stdout.getvalue(), "")
