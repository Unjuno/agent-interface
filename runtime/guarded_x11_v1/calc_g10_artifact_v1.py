"""Parent-held two-save custody for the fixed G10 Calc formula task.

This is an internal candidate seam. It is deliberately not registered in the
public MCP server yet. The parent snapshots each save immediately after its
release-verified action, then scores both immutable files only after exact
target exit and a verified close.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat

from .calc_effect_v1 import _read_regular
from .calc_g10_formula_effect_v1 import score_g10_fods_bytes
from .calc_task_artifact_v1 import _stable_directory, CalcTaskArtifact


PROFILE_ID = 'calc-g10-two-save-v1'
_DESCRIPTOR_SCHEMA = 'agent-interface/calc-g10-two-save-descriptor-v1'
_SAVE_REQUEST_SCHEMA = 'agent-interface/calc-g10-save-request-v1'
_ARTIFACT_NAME = 'task-artifact.fods'
_SNAPSHOT_NAMES = {'first': 'g10-first.fods', 'second': 'g10-second.fods'}
_CASES = {'first': (29, 31), 'second': (43, 47)}
_G10_BLANK = (
    b'<?xml version="1.0" encoding="UTF-8"?>'
    b'<office:document '
    b'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
    b'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
    b'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
    b'office:version="1.2" '
    b'office:mimetype="application/vnd.oasis.opendocument.spreadsheet">'
    b'<office:body><office:spreadsheet><table:table table:name="Sheet1">'
    b'<table:table-row>'
    b'<table:table-cell office:value-type="string"><text:p>a</text:p>'
    b'</table:table-cell>'
    b'<table:table-cell office:value-type="string"><text:p>b</text:p>'
    b'</table:table-cell>'
    b'<table:table-cell office:value-type="string"><text:p>product</text:p>'
    b'</table:table-cell></table:table-row>'
    b'<table:table-row table:number-rows-repeated="20">'
    b'<table:table-cell table:number-columns-repeated="20"/>'
    b'</table:table-row></table:table></office:spreadsheet></office:body>'
    b'</office:document>')


class CalcG10ArtifactCustody:
    """Keep two immutable save snapshots under one parent-owned task call."""

    def __init__(self, call_root, *, call_id, attempt_id):
        if type(call_id) is not str or not re.fullmatch(r'[0-9a-f]{32}', call_id):
            raise ValueError('invalid call ID')
        if (type(attempt_id) is not str
                or not re.fullmatch(r'[\x21-\x7e]{1,128}', attempt_id)):
            raise ValueError('invalid attempt ID')
        self.call_root = _stable_directory(call_root)
        if self.call_root.name != call_id:
            raise ValueError('call root does not match call ID')
        self.call_id = call_id
        self.attempt_id = attempt_id
        self._process_generation = None
        self._window_generation = None
        self._target_xid = None
        self._target_pid = None
        self._target_start_ticks = None
        self._records = {}
        self._verified = None
        self.workbook_path = self.call_root / _ARTIFACT_NAME
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_BINARY', 0)
        flags |= getattr(os, 'O_NOFOLLOW', 0)
        fd = os.open(self.workbook_path, flags, 0o600)
        try:
            view = memoryview(_G10_BLANK)
            while view:
                count = os.write(fd, view)
                if count <= 0:
                    raise OSError('short write reserving G10 blank workbook')
                view = view[count:]
            os.fsync(fd)
        finally:
            os.close(fd)
        blank, self._blank_identity = _read_regular(
            self.workbook_path, max_bytes=64 * 1024 * 1024)
        if blank != _G10_BLANK:
            raise ValueError('G10 blank workbook reservation changed')
        self._blank_sha256 = hashlib.sha256(blank).hexdigest()

    def bind_target(self, *, process_generation, window_generation,
                    target_xid, target_pid, target_start_ticks):
        if self._process_generation is not None:
            raise ValueError('G10 target identity already bound')
        try:
            blank, identity = _read_regular(
                self.workbook_path, max_bytes=64 * 1024 * 1024)
        except (OSError, ValueError, TypeError) as error:
            raise ValueError('G10 blank workbook changed before target binding') from error
        if blank != _G10_BLANK or identity != self._blank_identity:
            raise ValueError('G10 blank workbook changed before target binding')
        for value in (process_generation, window_generation):
            if type(value) is not str or not re.fullmatch(r'[0-9a-f]{64}', value):
                raise ValueError('exact process/window generations required')
        CalcTaskArtifact._validate_target_identity(
            target_xid, target_pid, target_start_ticks,
            process_generation=process_generation)
        self._process_generation = process_generation
        self._window_generation = window_generation
        self._target_xid = target_xid
        self._target_pid = target_pid
        self._target_start_ticks = target_start_ticks

    @property
    def descriptor(self):
        if self._process_generation is None:
            raise ValueError('G10 target identity is not bound')
        return {
            'schema': _DESCRIPTOR_SCHEMA,
            'profile_id': PROFILE_ID,
            'call_id': self.call_id,
            'attempt_id': self.attempt_id,
            'artifact_name': _ARTIFACT_NAME,
            'expected_actions': ['first', 'second'],
            'blank_sha256': self._blank_sha256,
            'blank_bytes': len(_G10_BLANK),
            'blank_identity': list(self._blank_identity),
            'process_generation': self._process_generation,
            'window_generation': self._window_generation,
            'target_xid': self._target_xid,
            'target_pid': self._target_pid,
            'target_start_ticks': self._target_start_ticks,
        }

    def record_saved_action(self, action, *, action_receipt, save_request):
        """Snapshot the current workbook after a matching released action.

        This method must be called by the parent controller at each completed
        graph action, before the next action can overwrite the workbook.
        """
        if self._verified is not None:
            raise ValueError('G10 custody is already terminal')
        expected_index = len(self._records)
        expected_actions = ('first', 'second')
        if (expected_index >= len(expected_actions)
                or action != expected_actions[expected_index]
                or action not in _CASES):
            raise ValueError('G10 saves must be captured once in first/second order')
        if self._process_generation is None:
            raise ValueError('G10 target identity is not bound')
        if (type(action_receipt) is not dict
                or action_receipt.get('action') != action
                or action_receipt.get('status') != 'completed'
                or action_receipt.get('release_verified') is not True
                or type(action_receipt.get('action_id')) is not str
                or not action_receipt['action_id']
                or len(action_receipt['action_id']) > 128):
            raise ValueError('G10 action receipt is not completed and released')
        required = {'schema', 'call_id', 'attempt_id', 'profile_id', 'action',
                    'action_id', 'process_generation', 'window_generation',
                    'save_request_id', 'save_request_monotonic_ns'}
        if (type(save_request) is not dict or set(save_request) != required
                or save_request.get('schema') != _SAVE_REQUEST_SCHEMA
                or save_request.get('call_id') != self.call_id
                or save_request.get('attempt_id') != self.attempt_id
                or save_request.get('profile_id') != PROFILE_ID
                or save_request.get('action') != action
                or save_request.get('action_id') != action_receipt['action_id']
                or save_request.get('process_generation') != self._process_generation
                or save_request.get('window_generation') != self._window_generation
                or type(save_request.get('save_request_id')) is not str
                or not re.fullmatch(r'[0-9a-f]{32}', save_request['save_request_id'])
                or type(save_request.get('save_request_monotonic_ns')) is not int
                or save_request['save_request_monotonic_ns'] <= 0):
            raise ValueError('G10 save request does not match its action and owner')
        if save_request['save_request_id'] in {
                row['save_request_id'] for row in self._records.values()}:
            raise ValueError('G10 save request ID reused')

        data, _source_identity = _read_regular(
            self.workbook_path, max_bytes=64 * 1024 * 1024)
        digest = hashlib.sha256(data).hexdigest()
        if digest == self._blank_sha256:
            raise ValueError('G10 workbook is unchanged from reserved blank')
        snapshot_path = self.call_root / _SNAPSHOT_NAMES[action]
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_BINARY', 0)
        flags |= getattr(os, 'O_NOFOLLOW', 0)
        fd = os.open(snapshot_path, flags, 0o600)
        try:
            view = memoryview(data)
            while view:
                count = os.write(fd, view)
                if count <= 0:
                    raise OSError('short write preserving G10 save snapshot')
                view = view[count:]
            os.fsync(fd)
        finally:
            os.close(fd)
        saved, identity = _read_regular(snapshot_path, max_bytes=64 * 1024 * 1024)
        if saved != data:
            raise ValueError('G10 snapshot differs from the saved workbook bytes')
        row = {
            'schema': 'agent-interface/calc-g10-save-receipt-v1',
            'call_id': self.call_id,
            'attempt_id': self.attempt_id,
            'profile_id': PROFILE_ID,
            'action': action,
            'action_id': action_receipt['action_id'],
            'action_release_verified': True,
            'process_generation': self._process_generation,
            'window_generation': self._window_generation,
            'save_request_id': save_request['save_request_id'],
            'save_request_monotonic_ns': save_request['save_request_monotonic_ns'],
            'artifact_name': _SNAPSHOT_NAMES[action],
            'artifact_sha256': digest,
            'artifact_bytes': len(saved),
            'artifact_identity': list(identity),
        }
        self._records[action] = row
        return dict(row)

    def verify_after_close(self, *, method_receipt, close_receipt,
                           target_exit_receipt):
        """Promote effect to task success only after both saves and exact exit."""
        if self._verified is not None:
            return dict(self._verified)
        unknown = {'status': 'unknown', 'task_success': None,
                   'replay_allowed': False, 'call_id': self.call_id,
                   'attempt_id': self.attempt_id, 'profile_id': PROFILE_ID}
        if (not isinstance(close_receipt, dict)
                or close_receipt.get('status') != 'closed'
                or close_receipt.get('verified') is not True
                or close_receipt.get('owner_process_retired') is not True
                or close_receipt.get('release_confirmed') is not True):
            return dict(unknown, reason='verified_close_required')
        if (self._process_generation is None
                or self._window_generation is None
                or self._target_xid is None
                or self._target_pid is None
                or self._target_start_ticks is None):
            return dict(unknown, reason='target_identity_unavailable')
        descriptor = self.descriptor
        if set(self._records) != {'first', 'second'}:
            return dict(unknown, reason='both_g10_save_receipts_required')
        if type(method_receipt) is not dict:
            return dict(unknown, reason='method_receipt_unavailable')
        transitions = method_receipt.get('transitions')
        if (method_receipt.get('format') != 'compiled-gui-runtime-receipt-v1'
                or method_receipt.get('outcome') != 'TASK_SUCCEEDED'
                or method_receipt.get('reason') != 'method_complete'
                or method_receipt.get('completed_transitions') != 2
                or type(transitions) is not list or len(transitions) != 2):
            return dict(unknown, reason='g10_method_receipt_invalid')
        for action, transition in zip(('first', 'second'), transitions):
            record = self._records[action]
            if (type(transition) is not dict
                    or transition.get('action') != action
                    or transition.get('action_id') != record['action_id']
                    or transition.get('release_verified') is not True):
                return dict(unknown, reason='g10_transition_receipt_mismatch')
        exit_common = {'status', 'verified', 'process_generation', 'xid',
                       'pid', 'start_ticks', 'exit_code',
                       'observed_monotonic_ns'}
        direct_exit_fields = exit_common | {'schema'}
        wrapped_exit_fields = exit_common | {
            'schema', 'custody', 'launcher_pid', 'launcher_start_ticks',
            'launcher_executable', 'launcher_package_version',
            'launcher_exit_code', 'replacement_observed'}
        exit_schema = (target_exit_receipt.get('schema')
                       if type(target_exit_receipt) is dict else None)
        if exit_schema == 'agent-interface/calc-target-exit-receipt-v1':
            exit_shape_valid = set(target_exit_receipt) == direct_exit_fields
        elif exit_schema == 'agent-interface/calc-target-exit-receipt-v2':
            exit_shape_valid = (
                set(target_exit_receipt) == wrapped_exit_fields
                and target_exit_receipt.get('custody')
                    == 'libreoffice-oosplash-direct-child-v1'
                and type(target_exit_receipt.get('launcher_pid')) is int
                and target_exit_receipt['launcher_pid'] > 0
                and target_exit_receipt['launcher_pid']
                    != target_exit_receipt.get('pid')
                and type(target_exit_receipt.get('launcher_start_ticks')) is int
                and target_exit_receipt['launcher_start_ticks'] > 0
                and type(target_exit_receipt.get('launcher_executable')) is str
                and target_exit_receipt['launcher_executable'].startswith('/')
                and target_exit_receipt.get('launcher_package_version')
                    == '4:7.4.7-1+deb12u14'
                and target_exit_receipt.get('launcher_exit_code')
                    == target_exit_receipt.get('exit_code')
                and target_exit_receipt.get('replacement_observed') is False)
        else:
            exit_shape_valid = False
        if (not exit_shape_valid
                or target_exit_receipt.get('status') != 'exited'
                or target_exit_receipt.get('verified') is not True
                or target_exit_receipt.get('process_generation')
                    != descriptor['process_generation']
                or target_exit_receipt.get('xid') != descriptor['target_xid']
                or target_exit_receipt.get('pid') != descriptor['target_pid']
                or target_exit_receipt.get('start_ticks')
                    != descriptor['target_start_ticks']
                or type(target_exit_receipt.get('exit_code')) is not int
                or target_exit_receipt['exit_code'] != 0
                or type(target_exit_receipt.get('observed_monotonic_ns')) is not int
                or target_exit_receipt['observed_monotonic_ns'] <= max(
                    row['save_request_monotonic_ns']
                    for row in self._records.values())):
            return dict(unknown, reason='target_process_exit_invalid')

        method_digest = hashlib.sha256(json.dumps(
            method_receipt, sort_keys=True, separators=(',', ':'),
            allow_nan=False).encode('utf-8')).hexdigest()
        effects = {}
        for action, (a, b) in _CASES.items():
            record = self._records[action]
            if (record.get('call_id') != self.call_id
                    or record.get('attempt_id') != self.attempt_id
                    or record.get('profile_id') != PROFILE_ID
                    or record.get('process_generation') != descriptor['process_generation']
                    or record.get('window_generation') != descriptor['window_generation']
                    or record.get('action_release_verified') is not True):
                return dict(unknown, reason='g10_save_receipt_identity_mismatch')
            path = self.call_root / _SNAPSHOT_NAMES[action]
            try:
                data, identity = _read_regular(path, max_bytes=64 * 1024 * 1024)
            except (OSError, ValueError, TypeError):
                return dict(unknown, reason='g10_snapshot_unavailable')
            digest = hashlib.sha256(data).hexdigest()
            if (digest != record['artifact_sha256']
                    or len(data) != record['artifact_bytes']
                    or list(identity) != record['artifact_identity']):
                return dict(unknown, reason='g10_snapshot_custody_mismatch')
            effect = score_g10_fods_bytes(data, a=a, b=b)
            effects[action] = {
                'action_id': record['action_id'],
                'save_request_id': record['save_request_id'],
                'save_request_monotonic_ns': record['save_request_monotonic_ns'],
                'method_receipt_sha256': method_digest,
                'artifact_sha256': digest,
                'effect': effect,
            }
        if any(row['effect']['status'] == 'unknown' for row in effects.values()):
            self._verified = dict(unknown, reason='g10_saved_effect_unknown',
                                  saved_effects=effects)
        elif any(row['effect']['effect_match'] is not True
                 for row in effects.values()):
            self._verified = {
                'status': 'failed', 'task_success': False,
                'replay_allowed': False, 'call_id': self.call_id,
                'attempt_id': self.attempt_id, 'profile_id': PROFILE_ID,
                'reason': 'g10_saved_effect_mismatch', 'saved_effects': effects,
            }
        else:
            self._verified = {
                'status': 'verified', 'task_success': True,
                'replay_allowed': False, 'call_id': self.call_id,
                'attempt_id': self.attempt_id, 'profile_id': PROFILE_ID,
                'reason': 'both_g10_saved_effects_verified',
                'saved_effects': effects,
            }
        return dict(self._verified)
