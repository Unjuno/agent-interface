from argparse import Namespace
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'live_control')]
import map01_overlap_controller_v39 as controller
import session_map01_v15 as session


class IdentitySelectionTests(unittest.TestCase):
    def arguments(self, measurement, selected):
        return Namespace(measurement_session=measurement, target_process_identity=selected,
                         seed=7, load_fixture_manifest=Path('fixture.json'))

    def test_controller_explicit_flag_reaches_measurement_session(self):
        command = controller.session_command(self.arguments(True, True), Path('out'))
        self.assertIn('--target-process-identity', command)
        self.assertIn('session_map01_v15.py', command[1])

    def test_legacy_default_and_invalid_selection(self):
        self.assertNotIn('--target-process-identity',
            controller.session_command(self.arguments(True, False), Path('out')))
        with self.assertRaises(ValueError):
            controller.session_command(self.arguments(False, True), Path('out'))

    def test_v15_selects_policy_strips_flag_and_pins_runtime_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / 'sources.json').write_text('{}')
            base = ModuleType('session_map01_v12')
            base.vd = SimpleNamespace(DoomGame=object, GameVariable=object)
            base.sys = SimpleNamespace(stdin=object())
            selected = ModuleType('doom_process_identity_backend_v1')
            selected.Backend = type('IdentityBackend', (), {})
            telemetry = ModuleType('doom_owner_thread_release_batch_backend_v1')
            telemetry.Backend = type('LegacyBackend', (), {})
            seen = []
            base.main = lambda: seen.append((base.Backend, list(sys.argv)))
            argv = ['session', '--out', directory, '--target-process-identity']
            with patch.dict(sys.modules, {'session_map01_v12': base,
                    'doom_process_identity_backend_v1': selected,
                    'doom_owner_thread_release_batch_backend_v1': telemetry}), patch.object(
                    session, 'MainThreadScorerStdin', return_value=Mock()), patch.object(
                    session, 'ScorerFileSink', return_value=Mock()), patch.object(sys, 'argv', argv):
                session.main()
                self.assertIs(sys.argv, argv)
            self.assertIs(seen[0][0], selected.Backend)
            self.assertNotIn('--target-process-identity', seen[0][1])
            sources = json.loads((output / 'sources.json').read_text())
            sources = {name.replace('\\', '/'): value for name, value in sources.items()}
            self.assertIn('doom/doom_process_identity_backend_v1.py', sources)
            self.assertIn('live_control/target_process_identity_v1.py', sources)
            self.assertFalse(any(name.startswith('repo/') for name in sources))
            identity_sources = json.loads((output / 'target-process-identity-sources.json').read_text())
            self.assertIn('runtime/guarded_x11_v1/process_identity.py', identity_sources['files'])
            self.assertIn('runtime/guarded_x11_v1/target_queries.py', identity_sources['files'])
