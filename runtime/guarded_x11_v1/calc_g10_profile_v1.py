"""Fixed two-save G10 profile built on the current guarded Calc owner.

This module contains trusted callbacks only. Public requests select this fixed
profile and supply reviewed aliases; they cannot supply graph code, OCR code,
tails, paths, or callback implementations.
"""
import re
import secrets
import shutil
import subprocess
import time
from pathlib import Path

from PIL import Image, ImageOps

from runtime.core_v1.compiled_gui import validate
from runtime.guarded_x11_v1.calc_g10_artifact_v1 import (
    PROFILE_ID, CalcG10ArtifactCustody,
    make_registered_calc_g10_save_controller_receipt,
)
from runtime.guarded_x11_v1.calc_profile_v1 import (
    CalcPrimaryProfile,
)
from runtime.guarded_x11_v1.process_identity import (
    process_generation_from_identity,
)
from runtime.cli_v1.attempt import _write_json

_CASES = {'first': ('29', '31', '899'), 'second': ('43', '47', '2021')}
_ROW = (36, 161, 305, 175)
_CELL_BOXES = ((37, 161, 124, 175), (127, 161, 215, 175),
               (217, 161, 305, 175))
_MAX_OCR_NS = 3_000_000_000


class CalcG10Profile:
    """One exact two-action/two-save task with parent-held byte custody."""

    def __init__(self, bridge, bindings, call_root, *, reviewed_sequence,
                 reviewed_artifact_sha256, blank_reviewed, call_id, attempt_id,
                 task_artifact, clock=time.monotonic_ns,
                 ocr_runner=subprocess.run):
        if not isinstance(task_artifact, CalcG10ArtifactCustody):
            raise ValueError('parent-created G10 artifact custody is required')
        if task_artifact.call_id != call_id or task_artifact.attempt_id != attempt_id:
            raise ValueError('G10 artifact belongs to another call or attempt')
        # Reuse the current profile's exact source, geometry, title, menu-anchor,
        # freshness and focus checks. G10 uses separate formula/save semantics.
        self.guard = CalcPrimaryProfile(bridge, bindings, call_root,
            reviewed_sequence=reviewed_sequence,
            reviewed_artifact_sha256=reviewed_artifact_sha256,
            blank_reviewed=blank_reviewed, clock=clock,
            call_id=None, attempt_id=None,
            task_values={'A1': '29', 'A2': '31'})
        native, image = bridge.history[reviewed_sequence]
        self.bridge = bridge
        self.call_root = Path(call_root).resolve()
        self.call_id = call_id
        self.attempt_id = attempt_id
        self.artifact = task_artifact
        self.clock = clock
        self.ocr_runner = ocr_runner
        self.ocr_executable = shutil.which('tesseract')
        if not self.ocr_executable:
            raise ValueError('trusted Tesseract executable is unavailable')
        self.entry_alias = bindings['entry']['alias']
        self.save_alias = bindings['save']['alias']
        self._validate_save_anchor(bridge, self.save_alias,
            bindings['save']['offset'], native, image, clock(),
            self.guard.reviewed_scope)
        self.bindings = self._bindings(bindings)
        self.completed = []
        self.dispatches = {}
        self.save_requests = {}
        self.save_receipts = []
        self.ocr_count = 0
        self.deadline_ns = self.clock() + 10_000_000_000
        self.blank_row = self.guard.bridge.history[reviewed_sequence][1].crop(_ROW).tobytes()
        self._bind_process_generation()
        self.interface = self._interface()

    @staticmethod
    def _validate_save_anchor(bridge, alias, offset, native, image,
                              now_ns, session_scope):
        resolution = bridge.store.resolve_point(alias, offset, native, image,
            now_ns, session_scope=session_scope)
        if not (resolution.get('eligible')
                and resolution.get('point') == [16, 31]
                and resolution.get('observed_box') == [4, 23, 24, 16]
                and offset == [12, 8]):
            raise ValueError('G10 save action must use the reviewed stable menu keyboard anchor')

    def _bind_process_generation(self):
        bridge = self.bridge
        binding = self.guard.reviewed_binding
        xid = self.guard.reviewed_window_id
        before = bridge.inspect_process_incarnation(xid)
        metadata = bridge.inspect_window_metadata(xid)
        after = bridge.inspect_process_incarnation(xid)
        process_generation = binding.get('process_generation')
        if (metadata.get('xid') != xid
                or metadata.get('process_incarnation') != before
                or after != before
                or metadata.get('process_generation') != process_generation
                or type(metadata.get('window_incarnation')) is not str
                or not re.fullmatch(r'[0-9a-f]{64}', metadata['window_incarnation'])
                or metadata.get('mapped') is not True
                or metadata.get('focused_before') is not True
                or metadata.get('focused_after') is not True):
            raise ValueError('G10 target process/window generation is not current')
        target_pid = metadata.get('process_pid')
        target_start_ticks = metadata.get('process_start_ticks')
        if process_generation != process_generation_from_identity(
                xid, target_pid, target_start_ticks):
            raise ValueError('G10 process generation does not match exact target identity')
        if self.artifact.process_generation is None:
            self.artifact.bind_target(
                process_generation=process_generation,
                window_generation=metadata['window_incarnation'],
                target_xid=xid, target_pid=target_pid,
                target_start_ticks=target_start_ticks)
        else:
            descriptor = self.artifact.descriptor
            expected = {
                'process_generation':process_generation,
                'window_generation':metadata['window_incarnation'],
                'target_xid':xid, 'target_pid':target_pid,
                'target_start_ticks':target_start_ticks}
            if any(descriptor.get(key) != value
                   for key, value in expected.items()):
                raise ValueError('G10 parent-bound target identity changed')

    def _bindings(self, references):
        action_bindings = {}
        for action, alias in (('first', 'entry'), ('second', 'save')):
            tail = [{'op': 'key_chord', 'keys': ['Down']},
                    {'op': 'text', 'text': _CASES[action][0], 'gap_ms': 20},
                    {'op': 'key_chord', 'keys': ['TAB']},
                    {'op': 'text', 'text': _CASES[action][1], 'gap_ms': 20},
                    {'op': 'key_chord', 'keys': ['TAB']},
                    {'op': 'text', 'text': '=A2*B2', 'gap_ms': 20},
                    {'op': 'key_chord', 'keys': ['ENTER']},
                    {'op': 'key_chord', 'keys': ['CTRL', 's']},
                    {'op': 'wait_update', 'timeout_ms': 300}]
            action_bindings[action] = {
                'interaction': 'keyboard',
                'offset': list(references[alias]['offset']),
                'tail': tail,
            }
        return action_bindings

    def _interface(self):
        from runtime.guarded_x11_v1.compiled import surface
        symbol = lambda alias: {
            'kind': 'target_reference', 'target_reference': alias,
            'identity_predicate': 'context_ok', 'dependencies': ['context_ok'],
        }
        def branch(when, outcome, action=None, next_state=None, reason=None):
            return {'when': when, 'outcome': outcome, 'action': action,
                    'next_state': next_state, 'reason': reason}
        return validate({
            'format': 'compiled-gui-interface-v1',
            'interface_id': PROFILE_ID,
            'session_scope': self.guard.reviewed_scope,
            'surface': surface(self.bridge),
            'predicates': ['context_ok', 'blank', 'row_match'],
            'symbols': {'first_target': symbol(self.entry_alias),
                        'second_target': symbol(self.save_alias)},
            'actions': {
                'first': {'target_symbol': 'first_target',
                          'operation': 'enter_and_save_g10_row',
                          'expected_effect': {'row_match': True}},
                'second': {'target_symbol': 'second_target',
                           'operation': 'replace_and_save_g10_row',
                           'expected_effect': {'row_match': True}},
            },
            'method': {
                'name': PROFILE_ID, 'version': '1',
                'initial_state': 'blank', 'max_transitions': 2,
                'max_runtime_ms': 10_000,
                'states': {
                    'blank': {'branches': [branch(
                        {'context_ok': True, 'blank': True}, 'action',
                        'first', 'first_saved')]},
                    'first_saved': {'branches': [branch(
                        {'context_ok': True, 'row_match': True}, 'action',
                        'second', 'second_saved')]},
                    'second_saved': {'branches': [branch(
                        {'context_ok': True, 'row_match': True}, 'complete')]},
                },
            },
        })

    def _current(self, native, image, *, active):
        if self.clock() >= self.deadline_ns:
            raise ValueError('G10 profile deadline expired')
        self.guard._read_current(native, image, allow_active=active,
                                 run_ocr=False)

    def _scan_row(self, image, *, sequence, action):
        if action not in _CASES:
            raise ValueError('G10 OCR action is not registered')
        expected = _CASES[action]
        deadline = min(self.deadline_ns, self.clock() + _MAX_OCR_NS)
        observed = []
        for index, box in enumerate(_CELL_BOXES):
            crop = ImageOps.expand(image.convert('RGB').crop(box).resize(
                ((box[2] - box[0]) * 4, (box[3] - box[1]) * 4),
                Image.Resampling.LANCZOS), border=20, fill='white')
            path = self.call_root / 'calc-g10-ocr'
            path.mkdir(parents=True, exist_ok=True)
            image_path = path / f'{sequence:06d}-{index}.png'
            crop.save(image_path)
            now = self.clock()
            if now >= deadline:
                raise ValueError('G10 OCR budget exhausted')
            result = self.ocr_runner(
                [self.ocr_executable, str(image_path), 'stdout', '--psm', '7',
                 '-l', 'eng', '-c', 'tessedit_char_whitelist=0123456789'],
                capture_output=True, text=True,
                timeout=(deadline - now) / 1_000_000_000, check=False)
            output = result.stdout.strip() if isinstance(result.stdout, str) else ''
            _write_json(path / f'{sequence:06d}-{index}.json', {
                'profile_id': PROFILE_ID, 'sequence': sequence,
                'cell_index': index, 'started_monotonic_ns': now,
                'ended_monotonic_ns': self.clock(),
                'returncode': result.returncode,
                'stdout': result.stdout, 'stderr': result.stderr,
                'expected_value': expected[index],
            })
            if (result.returncode != 0 or not output.isascii()
                    or not output.isdigit() or len(output) > 9):
                raise ValueError('G10 row OCR is missing, malformed, or ambiguous')
            observed.append(output)
        self.ocr_count += 3
        return observed == list(expected)

    def _predicates(self, native, image, *, active):
        self._current(native, image, active=active)
        blank = image.crop(_ROW).tobytes() == self.blank_row
        row_match = 'unknown'
        if self.dispatches:
            action = next(reversed(self.dispatches))
            row_match = self._scan_row(image,
                sequence=native['sequence'], action=action)
        return {'context_ok': True, 'blank': blank,
                'row_match': row_match}

    def perceive(self, native, image):
        try:
            return self._predicates(native, image, active=False)
        except (OSError, ValueError, KeyError, TypeError,
                subprocess.TimeoutExpired) as error:
            return {'context_ok': False, 'blank': False, 'row_match': 'unknown'}

    def guard_perceive(self, native, image):
        try:
            return self._predicates(native, image, active=True)
        except (OSError, ValueError, KeyError, TypeError,
                subprocess.TimeoutExpired):
            return {'context_ok': False, 'blank': False, 'row_match': 'unknown'}

    def verify_effect(self, request, _native, _image):
        observed = request.get('observation', {}).get('predicates', {})
        if observed.get('row_match') is True:
            return {'status': 'succeeded',
                    'evidence_ref': request['observation']['evidence_ref']}
        return {'status': 'unavailable',
                'evidence_ref': request['observation']['evidence_ref']}

    def verify_unchanged_effect(self, request, native, image):
        return self.verify_effect(request, native, image)

    def before_action_dispatch(self, dispatch):
        action = dispatch.get('action')
        if (action not in _CASES or action in self.save_requests
                or dispatch.get('profile_id') not in (None, PROFILE_ID)
                or dispatch.get('process_generation') != self.artifact.process_generation
                or dispatch.get('window_generation') != self.artifact.window_generation):
            raise ValueError('G10 pre-dispatch receipt is outside its exact attempt')
        request = {
            'schema': 'agent-interface/calc-g10-save-request-v2',
            'call_id': self.call_id, 'attempt_id': self.attempt_id,
            'profile_id': PROFILE_ID, 'action': action,
            'action_id': dispatch['action_id'],
            'process_generation': self.artifact.process_generation,
            'window_generation': self.artifact.window_generation,
            'save_request_id': secrets.token_hex(16),
            'save_request_monotonic_ns': dispatch['dispatch_started_ns'],
            'dispatch_evidence_ref': dispatch['evidence_ref'],
        }
        _write_json(self.call_root / f'g10-save-request-{action}.json', request)
        self.dispatches[action] = dict(dispatch)
        self.save_requests[action] = request

    def on_action_completed(self, transition):
        action = transition.get('action')
        if action not in _CASES or action in self.completed:
            raise ValueError('G10 action completion is duplicated or unknown')
        if action != ('first' if not self.completed else 'second'):
            raise ValueError('G10 actions must complete in first/second order')
        request = self.save_requests.get(action)
        dispatch = self.dispatches.get(action)
        if (not isinstance(request, dict) or not isinstance(dispatch, dict)
                or request['action_id'] != transition.get('action_id')
                or request['dispatch_evidence_ref'] != dispatch.get('evidence_ref')
                or transition.get('release_verified') is not True):
            raise ValueError('G10 action lacks its exact pre-dispatch/release join')
        receipt = self.artifact.record_saved_action(action,
            action_receipt={
                'action': action, 'action_id': transition['action_id'],
                'status': 'completed', 'release_verified': True,
                'dispatch_evidence_ref': request['dispatch_evidence_ref'],
            }, save_request=request)
        _write_json(self.call_root / f'g10-save-receipt-{action}.json', receipt)
        self.completed.append(action)
        self.save_receipts.append(receipt)

    def controller_receipt(self, method_receipt):
        if len(self.save_receipts) != 2:
            return None
        return make_registered_calc_g10_save_controller_receipt(
            descriptor=self.artifact.descriptor,
            method_receipt=method_receipt,
            save_receipts=self.save_receipts)
