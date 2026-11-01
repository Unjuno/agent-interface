"""Configuration gate for experimental owned-display MCP wiring."""
import tempfile
import unittest
from pathlib import Path

from runtime.cli_v1.mcp_server import create_server
from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner


class OwnedDisplayMcpOptionsTests(unittest.TestCase):
    def test_incomplete_or_incompatible_options_fail_before_creating_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            owner = PrivateDisplayOwner(base / 'display')
            valid = dict(session_mode='guarded-x11', display_name=':91',
                         guarded_owned_process=True, guarded_process_identity=True,
                         guarded_query_worker=True, guarded_prestarted_cancel_supervisor=True,
                         _guarded_display_owner=owner, _guarded_xauthority='/tmp/authority')
            cases = [
                {'_guarded_display_owner':None},
                {'_guarded_xauthority':None},
                {'_guarded_display_owner':object()},
                {'guarded_prestarted_cancel_supervisor':False},
                {'_guarded_owner_factory':lambda *_:None},
                {'_guarded_cancel_supervisor_target':lambda *_:None},
                {'session_mode':'one-shot'},
            ]
            for index, changes in enumerate(cases):
                with self.subTest(changes=changes):
                    options = dict(valid, **changes)
                    output = base / ('output-' + str(index))
                    with self.assertRaises(ValueError):
                        create_server({'app':1}, output, **options)
                    self.assertFalse(output.exists())
