"""Offline contracts for the fixed public G10 Calc profile callbacks."""
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from runtime.guarded_x11_v1.calc_g10_artifact_v1 import (
    CalcG10ArtifactCustody, PROFILE_ID,
)
from runtime.guarded_x11_v1.calc_g10_profile_v1 import CalcG10Profile
from runtime.guarded_x11_v1.process_identity import (
    process_generation_from_identity,
)
from runtime.guarded_x11_v1.test_compiled import Bridge


CALL_ID = 'e' * 32
ATTEMPT_ID = 'public-g10-profile-test'
XID, PID, START_TICKS = 42, 4321, 98765
PROCESS_GENERATION = process_generation_from_identity(XID, PID, START_TICKS)
WINDOW_GENERATION = 'f' * 64
FIXTURES = (Path(__file__).resolve().parents[2] / 'research' / 'integration'
            / 'calc_current_shared_3311_4d74_20261004'
            / 'calc-compiled-ocrlive-4d74' / 'runs' / 'compiled_ocrlive10')


class CalcG10ProfileTests(unittest.TestCase):
    def test_save_binding_must_be_the_reviewed_stable_menu_anchor(self):
        bridge = SimpleNamespace(store=SimpleNamespace(resolve_point=lambda *args,
            **kwargs: {'eligible': True, 'point': [16, 31],
                       'observed_box': [4, 23, 24, 16]}))
        CalcG10Profile._validate_save_anchor(bridge, 'save_alias', [12, 8],
            {}, Image.new('RGB', (1280, 800)), 1, 'scope')
        for point, box, offset in (
                ([200, 205], [190, 195, 20, 20], [10, 10]),
                ([16, 31], [4, 23, 24, 16], [0, 0])):
            bad_bridge = SimpleNamespace(store=SimpleNamespace(
                resolve_point=lambda *args, _point=point, _box=box, **kwargs:
                    {'eligible': True, 'point': _point, 'observed_box': _box}))
            with self.assertRaisesRegex(ValueError, 'stable menu keyboard anchor'):
                CalcG10Profile._validate_save_anchor(bad_bridge, 'save_alias',
                    offset, {}, Image.new('RGB', (1280, 800)), 1, 'scope')

    def test_interface_is_fixed_two_save_order_and_effect_gate(self):
        profile = CalcG10Profile.__new__(CalcG10Profile)
        profile.bridge = Bridge()
        profile.guard = SimpleNamespace(reviewed_scope=profile.bridge.scope)
        profile.entry_alias = 'stable_entry'
        profile.save_alias = 'stable_save'
        interface = profile._interface()
        self.assertEqual(interface['interface_id'], PROFILE_ID)
        self.assertEqual(list(interface['actions']), ['first', 'second'])
        self.assertEqual(interface['method']['max_transitions'], 2)
        self.assertEqual(interface['method']['states']['blank']['branches'][0]['action'],
                         'first')
        self.assertEqual(interface['method']['states']['first_saved']['branches'][0]['action'],
                         'second')
        self.assertEqual(interface['method']['states']['second_saved']['branches'][0]['outcome'],
                         'complete')
        self.assertEqual(interface['actions']['first']['expected_effect'],
                         {'row_match': True})
        self.assertEqual(interface['actions']['second']['expected_effect'],
                         {'row_match': True})

    def test_two_dispatches_join_released_actions_and_snapshot_in_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / CALL_ID
            root.mkdir()
            custody = CalcG10ArtifactCustody(root, call_id=CALL_ID,
                attempt_id=ATTEMPT_ID)
            custody.bind_target(process_generation=PROCESS_GENERATION,
                window_generation=WINDOW_GENERATION, target_xid=XID,
                target_pid=PID, target_start_ticks=START_TICKS)
            profile = CalcG10Profile.__new__(CalcG10Profile)
            profile.call_root = root
            profile.call_id = CALL_ID
            profile.attempt_id = ATTEMPT_ID
            profile.artifact = custody
            profile.completed = []
            profile.dispatches = {}
            profile.save_requests = {}
            profile.save_receipts = []
            for index, action in enumerate(('first', 'second'), start=1):
                timestamp = time.perf_counter_ns() + index * 10
                action_id = f'compiled-action-{index}'
                dispatch = {
                    'action': action, 'action_id': action_id,
                    'process_generation': PROCESS_GENERATION,
                    'window_generation': WINDOW_GENERATION,
                    'dispatch_started_ns': timestamp,
                    'evidence_ref': f'pre-dispatch-{index}',
                }
                profile.before_action_dispatch(dispatch)
                custody.workbook_path.write_bytes(
                    (FIXTURES / f'{action}.fods').read_bytes())
                profile.on_action_completed({
                    'action': action, 'action_id': action_id,
                    'release_verified': True,
                    'execution_started_ns': timestamp - 1,
                    'execution_accepted_ns': timestamp + 1,
                })
            self.assertEqual(profile.completed, ['first', 'second'])
            self.assertEqual([row['action'] for row in profile.save_receipts],
                             ['first', 'second'])
            self.assertEqual(
                [row['dispatch_evidence_ref'] for row in profile.save_receipts],
                ['pre-dispatch-1', 'pre-dispatch-2'])
            self.assertTrue((root / 'g10-first.fods').is_file())
            self.assertTrue((root / 'g10-second.fods').is_file())

    def test_dispatch_refuses_wrong_generation_before_persisting_request(self):
        profile = CalcG10Profile.__new__(CalcG10Profile)
        with tempfile.TemporaryDirectory() as directory:
            profile.call_root = Path(directory)
            profile.call_id = CALL_ID
            profile.attempt_id = ATTEMPT_ID
            profile.artifact = SimpleNamespace(
                process_generation=PROCESS_GENERATION,
                window_generation=WINDOW_GENERATION)
            profile.save_requests = {}
            profile.dispatches = {}
            with self.assertRaisesRegex(ValueError, 'exact attempt'):
                profile.before_action_dispatch({
                    'action': 'first', 'action_id': 'wrong-generation',
                    'process_generation': '0' * 64,
                    'window_generation': WINDOW_GENERATION,
                    'dispatch_started_ns': 1,
                    'evidence_ref': 'pre-dispatch',
                })
            self.assertEqual(profile.save_requests, {})
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_bounded_ocr_matches_each_fixed_g10_case_and_refuses_bad_text(self):
        with tempfile.TemporaryDirectory() as directory:
            profile = CalcG10Profile.__new__(CalcG10Profile)
            profile.call_root = Path(directory)
            profile.completed = ['first']
            profile.deadline_ns = time.monotonic_ns() + 10_000_000_000
            profile.clock = time.monotonic_ns
            profile.ocr_executable = 'tesseract'
            profile.ocr_count = 0
            outputs = iter(('29\n', '31\n', '899\n'))
            profile.ocr_runner = lambda *args, **kwargs: SimpleNamespace(
                returncode=0, stdout=next(outputs), stderr='')
            self.assertTrue(profile._scan_row(
                Image.new('RGB', (1280, 800), 'white'), sequence=7,
                action='first'))
            self.assertEqual(profile.ocr_count, 3)
            self.assertTrue((Path(directory) / 'calc-g10-ocr' / '000007-2.json').is_file())

            profile.completed = ['second']
            outputs = iter(('43\n', '47\n', 'wrong\n'))
            profile.ocr_runner = lambda *args, **kwargs: SimpleNamespace(
                returncode=0, stdout=next(outputs), stderr='')
            with self.assertRaisesRegex(ValueError, 'ambiguous'):
                profile._scan_row(Image.new('RGB', (1280, 800), 'white'),
                                  sequence=8, action='second')

    def test_effect_observation_uses_current_dispatch_before_completion_hook(self):
        profile = CalcG10Profile.__new__(CalcG10Profile)
        profile.deadline_ns = time.monotonic_ns() + 10_000_000_000
        profile.clock = time.monotonic_ns
        profile.completed = []
        profile.dispatches = {'first': {'action_id': 'first-id'}}
        image = Image.new('RGB', (1280, 800), 'white')
        profile.blank_row = b'not-the-current-row'
        seen = []
        profile._current = lambda *_args, **_kwargs: None
        def scan(_image, *, sequence, action):
            seen.append((sequence, action))
            return True
        profile._scan_row = scan
        first = profile._predicates({'sequence': 9}, image, active=False)
        self.assertTrue(first['row_match'])
        self.assertEqual(seen, [(9, 'first')])

        profile.completed.append('first')
        profile.dispatches['second'] = {'action_id': 'second-id'}
        second = profile._predicates({'sequence': 10}, image, active=False)
        self.assertTrue(second['row_match'])
        self.assertEqual(seen[-1], (10, 'second'))


if __name__ == '__main__':
    unittest.main()
