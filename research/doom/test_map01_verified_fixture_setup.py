"""Offline contract checks for the explicit verified fixture setup mode."""
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch


SOURCE = Path(__file__).with_name('session_map01_v12.py')


@lru_cache(maxsize=1)
def session_module():
    spec = importlib.util.spec_from_file_location('fixture_setup_session', SOURCE)
    module = importlib.util.module_from_spec(spec)
    old = sys.modules.get('vizdoom')
    sys.modules['vizdoom'] = types.ModuleType('vizdoom')
    try:
        spec.loader.exec_module(module)
    finally:
        if old is None:
            sys.modules.pop('vizdoom', None)
        else:
            sys.modules['vizdoom'] = old
    return module


class VerifiedFixtureSetupTests(unittest.TestCase):
    def test_setup_only_admits_one_predeclared_non_attack_move(self):
        session = session_module()
        move = [{'op': 'hold', 'keys': ['a'], 'duration_ms': 350}]
        expected = session.program_sha256(move)
        self.assertFalse(session.admit_verified_setup_program(
            [{'op': 'coast', 'duration_ms': 100, 'sample_ms': 50}], expected, False))
        self.assertTrue(session.admit_verified_setup_program(move, expected, False))
        with self.assertRaises(ValueError):
            session.admit_verified_setup_program(move, expected, True)
        for forbidden in ([{'op': 'hold', 'keys': ['space'], 'duration_ms': 100}],
                          [{'op': 'hold', 'keys': ['d'], 'duration_ms': 350}],
                          [{'op': 'pointer_click'}]):
            with self.subTest(program=forbidden), self.assertRaises(ValueError):
                session.admit_verified_setup_program(forbidden, expected, False)

    def test_setup_requires_explicit_gate_parent_and_new_target(self):
        session = session_module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            parent, target = root / 'parent.json', root / 'new.png'
            args = types.SimpleNamespace(verified_fixture_setup=True,
                                         load_fixture_manifest=parent, fixture_out=target,
                                         renewal_passive_observer=True,
                                         fixture_setup_program_sha256='a' * 64)
            session.validate_verified_fixture_setup(args, object())
            for gate, changed in ((None, args), (object(), types.SimpleNamespace(
                    verified_fixture_setup=True, load_fixture_manifest=None, fixture_out=target,
                    renewal_passive_observer=True,
                    fixture_setup_program_sha256='a' * 64))):
                with self.subTest(gate=gate), self.assertRaises(ValueError):
                    session.validate_verified_fixture_setup(changed, gate)
            target.with_suffix('.json').write_text('do not overwrite')
            with self.assertRaises(ValueError):
                session.validate_verified_fixture_setup(args, object())
            self.assertEqual(target.with_suffix('.json').read_text(), 'do not overwrite')

    def test_dangling_destination_symlink_is_not_followed(self):
        session = session_module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / 'fixture.png'
            target.symlink_to(root / 'missing.png')
            args = types.SimpleNamespace(verified_fixture_setup=True,
                                         load_fixture_manifest=root / 'parent.json', fixture_out=target,
                                         renewal_passive_observer=True,
                                         fixture_setup_program_sha256='a' * 64)
            with self.assertRaises(ValueError):
                session.validate_verified_fixture_setup(args, object())

    def test_pending_fixture_cannot_be_loaded_as_qualified(self):
        session = session_module()
        with tempfile.TemporaryDirectory() as temp:
            manifest = Path(temp) / 'fixture.json'
            manifest.write_text('{"schema":"map01_os_input_fixture_candidate_v1",'
                                '"setup_mode":"verified_loaded_fixture_setup_v1",'
                                '"qualification":"pending"}')
            with self.assertRaisesRegex(ValueError, 'not qualified'):
                session.validate_fixture_manifest(manifest, 'engine', 'wad', 1)
            manifest.write_text(manifest.read_text().replace('pending', 'qualified'))
            with self.assertRaisesRegex(ValueError, 'not qualified'):
                session.validate_fixture_manifest(manifest, 'engine', 'wad', 1)

    def test_pinned_directory_and_exclusive_candidate_outputs(self):
        session = session_module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            engine, frame = root / 'engine.tmp', root / 'frame.tmp'
            engine.write_bytes(b'engine')
            frame.write_bytes(b'frame')
            info = root.stat()
            identity = (info.st_dev, info.st_ino)
            target = root / 'fixture.png'
            fixture = {'qualification': 'pending'}
            with self.assertRaisesRegex(ValueError, 'directory changed'):
                session.write_verified_fixture(target, (info.st_dev, info.st_ino + 1), engine, frame, fixture)
            self.assertFalse(target.exists())
            session.write_verified_fixture(target, identity, engine, frame, fixture)
            self.assertEqual(target.read_bytes(), b'engine')
            self.assertEqual((root / 'fixture.source.png').read_bytes(), b'frame')
            self.assertEqual(json.loads((root / 'fixture.json').read_text())['qualification'], 'pending')
            with self.assertRaises(FileExistsError):
                session.write_verified_fixture(target, identity, engine, frame, fixture)
            self.assertEqual(target.read_bytes(), b'engine')

    def test_setup_requires_exact_completed_move_and_release(self):
        session = session_module()
        token = 'intent'
        accepted = {'event': 'accepted', 'id': 'move', 'intent_token': token,
                    'program_sha256': 'a' * 64}
        admission = {'event': 'input_admission', 'id': 'move', 'intent_token': token,
                     'owner_id': 'owner'}
        release = {'event': 'owner_release', 'verified': True, 'intent_token': token,
                   'keys_down': [], 'buttons_down': [], 'keys_unknown': [], 'key_state_errors': []}
        terminal = {'event': 'terminal', 'id': 'move', 'status': 'completed', 'release': release,
                    'input_owner_id': 'owner', 'input_owner_generation': 0}
        source = {'renewal_owner_id': 'owner', 'input_owner_generation': 0}
        gate = types.SimpleNamespace(first_press_observed=True,
                                     first_press=('move', 'owner', 123), first_press_intent=token)
        backend = types.SimpleNamespace(owner=types.SimpleNamespace(owner_id='owner'), _owner_generation=0)
        session.validate_setup_completed([accepted, admission, terminal], {'move': source}, gate,
                                         'a' * 64, accepted, terminal, backend)
        for wrong in ({**terminal, 'status': 'cancelled'},
                      {**terminal, 'input_owner_id': 'other'},
                      {**terminal, 'release': {**release, 'verified': False}}):
            with self.subTest(wrong=wrong), self.assertRaises(ValueError):
                session.validate_setup_completed([accepted, admission, wrong], {'move': source}, gate,
                                                 'a' * 64, accepted, wrong, backend)
        with self.assertRaises(ValueError):
            session.validate_setup_completed([], {}, gate, 'a' * 64, None, None, backend)
        bad_gate = types.SimpleNamespace(first_press_observed=True,
                                         first_press=('other', 'owner', 123), first_press_intent=token)
        with self.assertRaises(ValueError):
            session.validate_setup_completed([accepted, admission, terminal], {'move': source}, bad_gate,
                                             'a' * 64, accepted, terminal, backend)
        foreign = {'event': 'input_admission', 'id': 'other', 'owner_id': 'owner', 'intent_token': 'other'}
        with self.assertRaises(ValueError):
            session.validate_setup_completed([accepted, admission, terminal, foreign], {'move': source},
                                             gate, 'a' * 64, accepted, terminal, backend)
        backend.owner.owner_id = 'new-owner'
        with self.assertRaises(ValueError):
            session.validate_setup_completed([accepted, admission, terminal], {'move': source}, gate,
                                             'a' * 64, accepted, terminal, backend)

    def test_exclusive_copy_never_overwrites_existing_target(self):
        session = session_module()
        with tempfile.TemporaryDirectory() as temp:
            source, destination = Path(temp) / 'source', Path(temp) / 'destination'
            source.write_bytes(b'new')
            destination.write_bytes(b'existing')
            with self.assertRaises(FileExistsError):
                session.copy_file_exclusive(source, destination)
            self.assertEqual(destination.read_bytes(), b'existing')


if __name__ == '__main__':
    unittest.main()
