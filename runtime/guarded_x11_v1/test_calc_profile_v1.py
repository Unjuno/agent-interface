"""Offline contract tests for the one registered Calc OCR profile."""
import hashlib
import json
import io
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

from runtime.guarded_x11_v1.calc_profile_v1 import (
    PROFILE_ID, CalcPrimaryProfile, _CELL_BOXES, _ENTRY_ANCHOR, _cell_cue,
    validate_calc_task_values, verify_saved_fods)
from runtime.guarded_x11_v1.handles import TargetHandleStore
from runtime.guarded_x11_v1.process_identity import (
    process_generation_from_identity,process_incarnation_from_identity)


HEADER = b'level\tleft\ttop\twidth\theight\tconf\ttext\n'
FILLED = HEADER + b'5\t95\t146\t22\t12\t95\t731\n5\t95\t162\t22\t12\t95\t864\n'
ROI_FILLED = HEADER + b'5\t118\t6\t44\t24\t95\t731\n5\t118\t38\t44\t24\t95\t864\n'
TARGET_XID,TARGET_PID,TARGET_START_TICKS = 20,4321,98765
PROCESS_GENERATION = process_generation_from_identity(
    TARGET_XID,TARGET_PID,TARGET_START_TICKS)
PROCESS_INCARNATION = process_incarnation_from_identity(
    TARGET_PID,TARGET_START_TICKS)


def _profile_image():
    image = Image.new('RGB', (1280, 800), 'white')
    x0, y0, width, height = _ENTRY_ANCHOR['box']
    for y in range(height):
        for x in range(width):
            if (x + y) % 2:
                image.putpixel((x0 + x, y0 + y), (225,225,225))
    return image


class _Bridge:
    def __init__(self, image, native):
        self.scope = 'calc-owned-test'
        self.binding_revision = 1
        self.sequence = native['sequence']
        self.active = None
        self.review_required = False
        self.session = SimpleNamespace(recovery_required=False)
        self.backend = SimpleNamespace(targets={'app': SimpleNamespace(id=20)})
        self.target = 'app'
        self.history = {self.sequence: (native, image)}
        self.title = 'primary-values.xlsx — LibreOffice Calc'
        self.binding = {'surface': 20, 'focus': 21, 'geometry': [0, 0, 1280, 800],
                        'process_generation': PROCESS_GENERATION}
        self.process_incarnation = PROCESS_INCARNATION
        self.ocr_rows = [FILLED]
        self.store = TargetHandleStore(self.scope)
        self.store.mint('calc_entry', 'screen_chrome', [4,23,24,16], native,
                        image, time.monotonic_ns())

    def _binding(self):
        return dict(self.binding)

    def _focus_within_target(self):
        return True

    def _window_title(self):
        return self.title

    def inspect_process_incarnation(self, window_id):
        self.asserted_window_id = window_id
        return self.process_incarnation

    def inspect_window_metadata(self, window_id):
        return {'xid':window_id,'process_incarnation':self.process_incarnation,
                'process_generation':PROCESS_GENERATION,
                'process_pid':TARGET_PID,'process_start_ticks':TARGET_START_TICKS,
                'window_incarnation':'c'*64,'mapped':True,
                'focused_before':True,'focused_after':True}


class CalcProfileTests(unittest.TestCase):
    def test_fixed_profile_boxes_match_the_qualified_1280x800_calc_sheet(self):
        self.assertEqual(_CELL_BOXES,
            {'A1':(36,143,126,159),'A2':(36,160,126,177)})
        self.assertEqual(_ENTRY_ANCHOR, {'point':[16,31],
            'box':[4,23,24,16], 'offset':[12,8]})
        self.assertEqual(_cell_cue(FILLED.decode()), 'filled')
        old_rows = HEADER + b'5\t95\t185\t22\t12\t95\t731\n5\t95\t205\t22\t12\t95\t864\n'
        self.assertEqual(_cell_cue(old_rows.decode()), 'unknown')

    def test_task_values_are_bounded_and_drive_ocr_and_saved_effect_scoring(self):
        values = {'A1':'24680','A2':'13579'}
        custom_tsv = (HEADER + b'5\t95\t146\t22\t12\t95\t24680\n'
                      + b'5\t95\t162\t22\t12\t95\t13579\n')
        self.assertEqual(_cell_cue(custom_tsv.decode(), expected=values), 'filled')
        self.assertEqual(_cell_cue(FILLED.decode(), expected=values), 'wrong')
        for invalid in (
                {'A1':'1','A2':'2','A3':'3'},
                {'A1':'01','A2':'2'},
                {'A1':'1.5','A2':'2'},
                {'A1':'1','A2':'x'},
                {'A1':1,'A2':'2'},
                {}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_calc_task_values(invalid)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'task.fods'
            self._fods(path, a1=values['A1'], a2=values['A2'])
            self.assertEqual(verify_saved_fods(path, expected=values)['task_success'], True)
            self.assertEqual(verify_saved_fods(path)['task_success'], False)

    @staticmethod
    def _fods(path, *, a1='731', a2='864', extra=None, malformed=False,
              empty_repeats=False, populated_repeat=False):
        if malformed:
            path.write_bytes(b'not valid XML')
            return
        first = f'<table:table-cell office:value-type="float" office:value="{a1}"/>'
        second = f'<table:table-cell office:value-type="float" office:value="{a2}"/>'
        if extra is not None:
            second += f'<table:table-cell office:value-type="string"><text:p>{extra}</text:p></table:table-cell>'
        xml = ''.join((
            '<?xml version="1.0"?><office:document-content ',
            'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" ',
            'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" ',
            'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">',
            '<office:body><office:spreadsheet><table:table table:name="Sheet1">',
            '<table:table-row' + (' table:number-rows-repeated="2"' if populated_repeat else '')
            + '>' + first + '<table:table-cell/></table:table-row>',
            '<table:table-row>' + second
            + ('<table:table-cell table:number-columns-repeated="50"/>' if empty_repeats else '')
            + '</table:table-row>',
            '<table:table-row table:number-rows-repeated="100"/>' if empty_repeats else '',
            '</table:table></office:spreadsheet></office:body></office:document-content>'))
        path.write_text(xml, encoding='utf-8')

    def test_independent_saved_fods_verifier_scores_exact_cells(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'task.fods'
            self._fods(path)
            result = verify_saved_fods(path)
            self.assertEqual(result['status'], 'verified')
            self.assertIs(result['task_success'], True)
            self.assertEqual(result['cells'], {'A1':'731','A2':'864'})
            self.assertEqual(len(result['artifact_sha256']), 64)

    def test_independent_saved_fods_verifier_compares_numeric_values_semantically(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'task.fods'
            self._fods(path, a1='731.0', a2='8.64E2')
            self.assertEqual(verify_saved_fods(path)['task_success'], True)
            self._fods(path, a1='NaN')
            result = verify_saved_fods(path)
            self.assertEqual((result['status'], result['task_success']), ('unknown', None))

    def test_independent_saved_fods_verifier_distinguishes_wrong_extra_and_missing(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'task.fods'
            self._fods(path, a2='863')
            wrong = verify_saved_fods(path)
            self.assertEqual((wrong['status'], wrong['reason']),
                             ('failed', 'cell_value_mismatch'))
            self._fods(path, extra='unexpected')
            extra = verify_saved_fods(path)
            self.assertEqual((extra['status'], extra['reason']),
                             ('failed', 'populated_cell_set_mismatch'))
            path.unlink()
            missing = verify_saved_fods(path)
            self.assertEqual((missing['status'], missing['task_success']),
                             ('unknown', None))

    def test_independent_saved_fods_verifier_treats_corrupt_or_ambiguous_as_unknown(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'task.fods'
            self._fods(path, malformed=True)
            self.assertEqual(verify_saved_fods(path)['task_success'], None)
            self._fods(path)
            path.write_text('<invalid/>', encoding='utf-8')
            self.assertEqual(verify_saved_fods(path)['task_success'], None)

    def test_independent_saved_fods_verifier_refuses_formula_cells(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'task.fods'
            self._fods(path)
            text = path.read_text(encoding='utf-8').replace(
                'office:value="731"',
                'table:formula="of:=1+730" office:value="731"')
            path.write_text(text, encoding='utf-8')
            result = verify_saved_fods(path)
            self.assertEqual((result['status'], result['task_success']), ('unknown', None))

    def test_independent_saved_fods_verifier_reads_retained_flat_xml_and_holds_formula(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'retained-flat.xml'
            self._fods(path)
            text = path.read_text(encoding='utf-8').replace(
                'office:value="731"',
                'table:formula="of:=1+730" office:value="731"')
            path.write_text(text, encoding='utf-8')
            result = verify_saved_fods(path)
            self.assertEqual((result['status'], result['task_success'], result['reason']),
                             ('unknown', None, 'formula_cells_unsupported'))

    def test_independent_saved_fods_verifier_allows_repeated_empty_cells_only(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'task.fods'
            self._fods(path, empty_repeats=True)
            self.assertEqual(verify_saved_fods(path)['task_success'], True)
            self._fods(path, populated_repeat=True)
            result = verify_saved_fods(path)
            self.assertEqual((result['status'], result['task_success']), ('unknown', None))

    def _source(self, root, sequence, image, binding):
        path = root / f'{sequence}.png'
        data = io.BytesIO()
        image.save(data, format='PNG')
        blob = data.getvalue()
        path.write_bytes(blob)
        digest = hashlib.sha256(blob).hexdigest()
        raw_digest = hashlib.sha256(b'raw-' + str(sequence).encode()).hexdigest()
        now = time.monotonic_ns()
        return {
            'sequence': sequence, 'capture_ns': now - 2_000_000,
            'binding_revision': 1, 'pointer_binding': dict(binding),
            'native': {'sha256': raw_digest, 'frame': 'screen_physical_px',
                'region': [0, 0, 1280, 800], 'width': 1280, 'height': 800,
                'native_window_id': 20, 'capture_ended_ns': now - 1_000_000,
                'artifact': {'path': str(path), 'sha256': digest,
                    'source_raw_sha256': raw_digest, 'bytes': len(blob),
                    'mime_type': 'image/png', 'width': 1280, 'height': 800}}}, blob

    def test_tsv_cue_distinguishes_match_wrong_and_unknown(self):
        self.assertEqual(_cell_cue(FILLED.decode()), 'filled')
        self.assertEqual(_cell_cue(ROI_FILLED.decode(),
                                   coordinate_origin=(36, 143),
                                   coordinate_scale=2), 'filled')
        self.assertEqual(_cell_cue(FILLED.replace(b'864', b'863').decode()), 'wrong')
        self.assertEqual(_cell_cue(HEADER.decode()), 'unknown')
        self.assertEqual(_cell_cue(FILLED.replace(b'95\t731', b'45\t731').decode()), 'unknown')

    def test_profile_is_fixed_and_save_requires_semantic_cells(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            image = _profile_image()
            binding = {'surface': 20, 'focus': 21, 'geometry': [0, 0, 1280, 800],
                       'process_generation': PROCESS_GENERATION}
            native, _ = self._source(root, 1, image, binding)
            image = Image.open(native['native']['artifact']['path']).convert('RGB')
            bridge = _Bridge(image, native)
            values = {'A1':'24680','A2':'13579'}
            roi_filled = ROI_FILLED.replace(b'731', b'24680').replace(b'864', b'13579')
            bridge.ocr_rows = [HEADER, roi_filled, roi_filled]
            ocr_calls = []
            def ocr(command, **kwargs):
                ocr_calls.append((command, kwargs))
                return SimpleNamespace(returncode=0, stdout=bridge.ocr_rows.pop(0), stderr=b'')
            bindings = {'entry': {'alias': 'calc_entry', 'offset': [12, 8]},
                        'save': {'alias': 'calc_save', 'offset': [3, 3]}}
            with patch('runtime.guarded_x11_v1.calc_profile_v1.shutil.which', return_value='tesseract'):
                profile = CalcPrimaryProfile(bridge, bindings, root,
                    reviewed_sequence=1,
                    reviewed_artifact_sha256=native['native']['artifact']['sha256'],
                    blank_reviewed=True, ocr_runner=ocr, task_values=values)
            self.assertEqual(profile.interface['interface_id'], PROFILE_ID)
            self.assertEqual(profile.interface['method']['max_transitions'], 2)
            self.assertEqual(profile.interface['method']['max_runtime_ms'], 10000)
            self.assertEqual(profile.bindings['enter']['interaction'], 'keyboard')
            self.assertEqual(profile.bindings['enter']['tail'][0],
                             {'op':'text','text':'24680','gap_ms':1})
            self.assertEqual(profile.bindings['enter']['tail'][3],
                             {'op':'text','text':'13579','gap_ms':1})
            self.assertNotIn({'op':'key_chord','keys':['Left']},
                             profile.bindings['enter']['tail'])
            self.assertIn('cells_filled', profile.interface['symbols']['save']['dependencies'])
            initial = profile.perceive(native, image.copy())
            self.assertEqual(initial, {'context_ok': True, 'blank': True,
                                       'cells_filled': 'unknown'})

            changed = image.copy()
            changed.paste((20, 20, 20), (40, 145, 50, 155))
            native2, _ = self._source(root, 2, changed, binding)
            bridge.sequence = 2
            bridge.history[2] = (native2, changed)
            stable_entry = bridge.store.resolve_point('calc_entry', [12,8],
                native2, changed, time.monotonic_ns(), session_scope=bridge.scope)
            self.assertTrue(stable_entry['eligible'], stable_entry)
            self.assertEqual(stable_entry['point'], [16,31], stable_entry)
            self.assertEqual(profile.perceive(native2, changed.copy()),
                {'context_ok': True, 'blank': False, 'cells_filled': True})
            bridge.active = ('calc_save', [3, 3])
            native3, _ = self._source(root, 3, changed, binding)
            bridge.sequence = 3
            bridge.history[3] = (native3, changed)
            guarded = profile.guard_perceive(native3, changed.copy())
            self.assertEqual(guarded,
                {'context_ok': True, 'blank': False, 'cells_filled': True})
            bridge.title = 'Confirm File Format — LibreOffice Calc'
            native4, _ = self._source(root, 4, changed, binding)
            bridge.sequence = 4
            bridge.history[4] = (native4, changed)
            self.assertEqual(profile.guard_perceive(native4, changed.copy()),
                {'context_ok': False, 'blank': False, 'cells_filled': 'unknown'})
            self.assertEqual(len(bridge.ocr_rows), 0)
            self.assertEqual(profile.verify_effect(
                {'action': 'save', 'observation': {'predicates': {'cells_filled': True}}},
                native2, changed)['status'], 'unavailable')
            self.assertTrue(ocr_calls)
            self.assertIn('--psm', ocr_calls[0][0])
            self.assertIn('6', ocr_calls[0][0])
            self.assertIn('tessedit_char_whitelist=0123456789', ocr_calls[0][0])
            roi = Image.open(io.BytesIO(ocr_calls[0][1]['input']))
            self.assertEqual(roi.mode, 'L')
            self.assertEqual(roi.size, (180, 68))

    def test_unchanged_frame_verifies_only_nonvisual_save_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            image = _profile_image()
            binding = {'surface': 20, 'focus': 21, 'geometry': [0, 0, 1280, 800],
                       'process_generation': PROCESS_GENERATION}
            native, _ = self._source(root, 1, image, binding)
            image = Image.open(native['native']['artifact']['path']).convert('RGB')
            bridge = _Bridge(image, native)
            with patch('runtime.guarded_x11_v1.calc_profile_v1.shutil.which',
                       return_value='tesseract'):
                profile = CalcPrimaryProfile(
                    bridge, {'entry': {'alias':'calc_entry','offset':[12,8]},
                             'save': {'alias':'calc_save','offset':[3,3]}},
                    root, reviewed_sequence=1,
                    reviewed_artifact_sha256=native['native']['artifact']['sha256'],
                    blank_reviewed=True, ocr_runner=lambda *_a, **_kw: None)
            requests = []

            def record_save_request(**kwargs):
                requests.append(kwargs)
                return {'schema':'agent-interface/calc-task-save-request-v1',
                        'save_request_id':'a'*32}

            profile.task_artifact = SimpleNamespace(
                record_save_request=record_save_request)
            profile.task_process_generation = 'b'*64
            profile.task_window_generation = 'c'*64
            observation = {'evidence_ref':'observation-unchanged',
                           'predicates':{'cells_filled':True}}
            request = {'action':'save','observation':observation}
            verdict = profile.verify_unchanged_effect(request, native, image)
            self.assertEqual(verdict, {'status':'unavailable',
                'evidence_ref':'observation-unchanged'})
            self.assertEqual(requests, [{'process_generation':'b'*64,
                                         'window_generation':'c'*64}])
            self.assertEqual(profile.task_save_request['save_request_id'],'a'*32)

            enter_verdict = profile.verify_unchanged_effect(
                {'action':'enter','observation':observation}, native, image)
            self.assertEqual(enter_verdict['status'],'unavailable')
            self.assertEqual(len(requests),1)

    def test_source_change_yields_unknown_without_reusing_ocr(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            image = _profile_image()
            binding = {'surface': 20, 'focus': 21, 'geometry': [0, 0, 1280, 800],
                       'process_generation': PROCESS_GENERATION}
            native, _ = self._source(root, 1, image, binding)
            image = Image.open(native['native']['artifact']['path']).convert('RGB')
            bridge = _Bridge(image, native)
            calls = []
            def ocr(*_args, **_kwargs):
                calls.append(True)
                return SimpleNamespace(returncode=0, stdout=FILLED, stderr=b'')
            bindings = {'entry': {'alias': 'calc_entry', 'offset': [12, 8]},
                        'save': {'alias': 'calc_save', 'offset': [3, 3]}}
            with patch('runtime.guarded_x11_v1.calc_profile_v1.shutil.which', return_value='tesseract'):
                profile = CalcPrimaryProfile(bridge, bindings, root,
                    reviewed_sequence=1,
                    reviewed_artifact_sha256=native['native']['artifact']['sha256'],
                    blank_reviewed=True, ocr_runner=ocr)
            profile.perceive(native, image.copy())
            native2, _ = self._source(root, 2, image, binding)
            bridge.sequence = 2
            bridge.history[2] = (native2, image.copy())
            bridge.title = 'Confirm File Format — LibreOffice Calc'
            result = profile.perceive(native2, image.copy())
            self.assertFalse(result['context_ok'])
            self.assertEqual(result['cells_filled'], 'unknown')
            self.assertEqual(len(calls), 1)

    def test_entry_guard_skips_ocr_but_save_guard_keeps_it_and_records_both(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            image = _profile_image()
            binding = {'surface': 20, 'focus': 21, 'geometry': [0, 0, 1280, 800],
                       'process_generation': PROCESS_GENERATION}
            native, _ = self._source(root, 1, image, binding)
            image = Image.open(native['native']['artifact']['path']).convert('RGB')
            bridge = _Bridge(image, native)
            calls = []

            def ocr(command, **kwargs):
                calls.append((command, kwargs))
                return SimpleNamespace(returncode=0, stdout=ROI_FILLED, stderr=b'')

            bindings = {'entry': {'alias': 'calc_entry', 'offset': [12, 8]},
                        'save': {'alias': 'calc_save', 'offset': [3, 3]}}
            with patch('runtime.guarded_x11_v1.calc_profile_v1.shutil.which', return_value='tesseract'):
                profile = CalcPrimaryProfile(bridge, bindings, root,
                    reviewed_sequence=1,
                    reviewed_artifact_sha256=native['native']['artifact']['sha256'],
                    blank_reviewed=True, ocr_runner=ocr)

            bridge.active = ('calc_entry', [12, 8])
            entry_native, _ = self._source(root, 2, image, binding)
            bridge.sequence = 2
            bridge.history[2] = (entry_native, image.copy())
            entry = profile.guard_perceive(entry_native, image.copy())
            self.assertEqual(entry, {'context_ok': True, 'blank': True,
                                     'cells_filled': 'unknown'})
            self.assertEqual(calls, [])
            skipped = json.loads((root / 'calc-ocr' / '001.json').read_text())
            self.assertEqual(skipped['artifact_sha256'],
                             entry_native['native']['artifact']['sha256'])
            self.assertEqual(skipped['ocr_status'], 'not_run')
            self.assertIs(skipped['ocr_invoked'], False)
            self.assertIs(skipped['authority_granted'], False)

            filled = image.copy()
            filled.paste((20, 20, 20), (40, 145, 50, 155))
            bridge.active = ('calc_save', [3, 3])
            save_native, _ = self._source(root, 3, filled, binding)
            bridge.sequence = 3
            bridge.history[3] = (save_native, filled.copy())
            saved = profile.guard_perceive(save_native, filled.copy())
            self.assertEqual(saved, {'context_ok': True, 'blank': False,
                                     'cells_filled': True})
            self.assertEqual(len(calls), 1)
            invoked = json.loads((root / 'calc-ocr' / '002.json').read_text())
            self.assertEqual(invoked['artifact_sha256'],
                             save_native['native']['artifact']['sha256'])
            self.assertIs(invoked['ocr_invoked'], True)
            self.assertEqual(profile.ocr_count, 1)

            bridge.active = ('calc_entry', [12, 8])
            bridge.title = 'Confirm File Format — LibreOffice Calc'
            stale_native, _ = self._source(root, 4, filled, binding)
            bridge.sequence = 4
            bridge.history[4] = (stale_native, filled.copy())
            refused = profile.guard_perceive(stale_native, filled.copy())
            self.assertFalse(refused['context_ok'])
            self.assertEqual(refused['cells_filled'], 'unknown')
            self.assertEqual(len(calls), 1)
            rejected = json.loads((root / 'calc-ocr' / '003.json').read_text())
            self.assertEqual(rejected['ocr_status'], 'unknown')
            self.assertIs(rejected['authority_granted'], False)

    def test_unreviewed_blank_and_malformed_bindings_refuse_preflight(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            image = _profile_image()
            binding = {'surface': 20, 'focus': 21, 'geometry': [0, 0, 1280, 800]}
            native, _ = self._source(root, 1, image, binding)
            image = Image.open(native['native']['artifact']['path']).convert('RGB')
            bridge = _Bridge(image, native)
            args = dict(reviewed_sequence=1,
                reviewed_artifact_sha256=native['native']['artifact']['sha256'],
                blank_reviewed=False)
            with patch('runtime.guarded_x11_v1.calc_profile_v1.shutil.which', return_value='tesseract'):
                with self.assertRaisesRegex(ValueError, 'blank-sheet review'):
                    CalcPrimaryProfile(bridge, {}, root, **args)


if __name__ == '__main__':
    unittest.main()
