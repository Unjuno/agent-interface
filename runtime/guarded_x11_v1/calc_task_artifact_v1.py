"""Parent-held admission and post-close scoring for one Calc task artifact.

This helper does not open Calc or certify that a GUI save occurred. Its result
is always task_success=None until parent-held receipts prove the exact Calc
process exited and a trusted call-bound Save controller proves the document
and save lifecycle. Parsed bytes are a separate cue.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import time

from .calc_effect_v1 import _read_regular
from .calc_profile_v1 import validate_calc_task_values, verify_saved_fods_bytes


_ARTIFACT_NAME = 'task-artifact.fods'
_DESCRIPTOR_SCHEMA = 'agent-interface/calc-task-artifact-descriptor-v1'
_SAVE_REQUEST_SCHEMA = 'agent-interface/calc-task-save-request-v1'
_SAVE_CONTROLLER_SCHEMA = 'agent-interface/calc-registered-save-controller-v1'
_BLANK_FODS = (b'<?xml version="1.0" encoding="UTF-8"?>'
    b'<office:document '
    b'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
    b'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
    b'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
    b'office:version="1.3" '
    b'office:mimetype="application/vnd.oasis.opendocument.spreadsheet">'
    b'<office:meta/><office:settings/><office:scripts/>'
    b'<office:font-face-decls/><office:styles/><office:automatic-styles/>'
    b'<office:body><office:spreadsheet>'
    b'<table:calculation-settings/><table:table table:name="Sheet1">'
    b'<table:table-row><table:table-cell/><table:table-cell/></table:table-row>'
    b'<table:table-row><table:table-cell/><table:table-cell/></table:table-row>'
    b'</table:table></office:spreadsheet></office:body></office:document>')


def _stable_directory(path):
    candidate = Path(path)
    info = candidate.lstat()
    if not stat.S_ISDIR(info.st_mode) or candidate.is_symlink():
        raise ValueError('call root must be a non-symlink directory')
    resolved = candidate.resolve(strict=True)
    if resolved != candidate.absolute():
        raise ValueError('call root path is not canonical')
    return resolved


def _plan_save_receipt_contract(interface):
    """Extract the only accepted two-action receipt shape from a bound plan."""
    from runtime.core_v1.compiled_gui import validate
    try:
        interface = validate(interface)
    except (TypeError, ValueError, KeyError):
        return None
    by_operation = {}
    for name, action in interface['actions'].items():
        operation = action['operation']
        if operation in by_operation:
            return None
        by_operation[operation] = name
    if set(by_operation) != {'enter_pair', 'request_save'}:
        return None
    method = interface['method']
    states = method['states']
    initial = method['initial_state']
    entry_name, save_name = by_operation['enter_pair'], by_operation['request_save']
    first = states[initial]['branches']
    if len(first) != 1 or first[0].get('action') != entry_name:
        return None
    intermediate = first[0].get('next_state')
    second = states.get(intermediate, {}).get('branches', [])
    if len(second) != 1 or second[0].get('action') != save_name:
        return None
    saved = second[0].get('next_state')
    final = states.get(saved, {}).get('branches', [])
    if (len(final) != 1 or final[0].get('outcome') != 'yield'
            or final[0].get('reason') != 'effect_unavailable'):
        return None
    if (first[0].get('when') != {'context_ok': True, 'blank': True}
            or second[0].get('when') != {'context_ok': True, 'cells_match': True}
            or interface['actions'][entry_name].get('expected_effect') != {'cells_match': True}
            or interface['actions'][save_name].get('expected_effect') != {'cells_match': True}):
        return None
    return {'interface': interface, 'entry_action': entry_name,
        'save_action': save_name, 'initial_state': initial,
        'intermediate_state': intermediate,
        'entry_when': first[0]['when'], 'save_when': second[0]['when']}


def make_registered_calc_save_controller_receipt(*, descriptor, method_receipt,
                                                   save_request,
                                                   parent_task_plan=None,
                                                   parent_task_plan_sha256=None):
    """Bind a parent-retained fixed-profile save dispatch to its exact call.

    The receipt is an in-memory server value. Callers cannot submit one through
    MCP. Only the registered Calc graph's successful entry effect, completed
    released Save action, bounded unavailable save-effect handoff, and matching
    call-owned request can mint it. Persisted bytes and clean target exit are
    still checked separately by the post-close verifier.
    """
    if (type(descriptor) is not dict or type(method_receipt) is not dict
            or type(save_request) is not dict):
        return None
    call_id = descriptor.get('call_id')
    attempt_id = descriptor.get('attempt_id')
    process_generation = descriptor.get('process_generation')
    window_generation = descriptor.get('window_generation')
    identity = (call_id, attempt_id, process_generation, window_generation)
    if (descriptor.get('profile_id') != 'calc-ocr-save-v1'
            or method_receipt.get('format') != 'compiled-gui-runtime-receipt-v1'
            or method_receipt.get('outcome') != 'SAFE_YIELD'
            or method_receipt.get('reason') != 'effect_unavailable'
            or method_receipt.get('completed_transitions') != 2
            or any(type(value) is not str or not value
                   for value in identity)
            or save_request.get('schema') != _SAVE_REQUEST_SCHEMA
            or tuple(save_request.get(key) for key in
                ('call_id','attempt_id','process_generation','window_generation')) != identity
            or type(save_request.get('save_request_id')) is not str
            or not re.fullmatch(r'[0-9a-f]{32}', save_request['save_request_id'])
            or type(save_request.get('save_request_monotonic_ns')) is not int
            or save_request['save_request_monotonic_ns'] <= 0):
        return None

    task_plan_digest = descriptor.get('task_plan_sha256')
    plan_contract = None
    if task_plan_digest is None:
        if (parent_task_plan is not None or parent_task_plan_sha256 is not None
                or method_receipt.get('task_plan_sha256') is not None
                or method_receipt.get('task_plan_interface') is not None
                or method_receipt.get('interface_id') != 'calc-ocr-save-v1'
                or method_receipt.get('method') != 'calc-ocr-save-v1'
                or method_receipt.get('method_version') != '1'):
            return None
    else:
        if (type(parent_task_plan) is not dict
                or parent_task_plan_sha256 != task_plan_digest
                or method_receipt.get('task_plan_sha256') != task_plan_digest
                or type(method_receipt.get('task_plan_interface')) is not dict):
            return None
        interface = method_receipt['task_plan_interface']
        symbols = interface.get('symbols')
        if type(symbols) is not dict:
            return None
        aliases = {}
        for symbol in symbols.values():
            if type(symbol) is not dict or symbol.get('kind') != 'target_reference':
                return None
            role = ('entry' if symbol.get('dependencies') == ['context_ok'] else
                    'save' if symbol.get('dependencies') == ['context_ok','cells_match']
                    else None)
            if role is None or role in aliases:
                return None
            aliases[role] = symbol.get('target_reference')
        if set(aliases) != {'entry','save'}:
            return None
        from .calc_symbolic_plan_v1 import validate_and_bind_calc_plan
        try:
            rebound = validate_and_bind_calc_plan(parent_task_plan,
                session_scope=interface['session_scope'],
                surface=interface['surface'], target_aliases=aliases)
        except (TypeError, ValueError, KeyError):
            return None
        if (rebound['plan_sha256'] != task_plan_digest
                or rebound['interface'] != interface
                or method_receipt.get('interface_id') != interface['interface_id']
                or method_receipt.get('method') != interface['method']['name']
                or method_receipt.get('method_version') != interface['method']['version']):
            return None
        plan_contract = _plan_save_receipt_contract(interface)
        if plan_contract is None:
            return None

    events = method_receipt.get('critical_events')
    if type(events) is not list or len(events) != 7:
        return None
    branch_enter, enter_terminal, enter_effect, branch_save, save_terminal, save_effect, finished = events
    if not all(type(row) is dict for row in events):
        return None
    entry_action = plan_contract['entry_action'] if plan_contract else 'enter'
    save_action = plan_contract['save_action'] if plan_contract else 'save'
    initial_state = plan_contract['initial_state'] if plan_contract else 'initial'
    intermediate_state = plan_contract['intermediate_state'] if plan_contract else 'filled'
    entry_when = plan_contract['entry_when'] if plan_contract else {'blank':True,'context_ok':True}
    save_when = plan_contract['save_when'] if plan_contract else {'cells_filled':True,'context_ok':True}
    if not (branch_enter.get('event') == 'branch_selected'
            and branch_enter.get('state') == initial_state
            and branch_enter.get('action') == entry_action
            and branch_enter.get('outcome') == 'action'
            and branch_enter.get('matched_conditions') == entry_when
            and enter_terminal.get('event') == 'action_terminal'
            and enter_terminal.get('action') == entry_action
            and enter_terminal.get('status') == 'completed'
            and enter_terminal.get('release_verified') is True
            and type(enter_terminal.get('action_id')) is str
            and enter_effect.get('event') == 'effect_checked'
            and enter_effect.get('action') == entry_action
            and enter_effect.get('action_id') == enter_terminal['action_id']
            and enter_effect.get('status') == 'succeeded'
            and branch_save.get('event') == 'branch_selected'
            and branch_save.get('state') == intermediate_state
            and branch_save.get('action') == save_action
            and branch_save.get('outcome') == 'action'
            and branch_save.get('matched_conditions') == save_when
            and save_terminal.get('event') == 'action_terminal'
            and save_terminal.get('action') == save_action
            and save_terminal.get('status') == 'completed'
            and save_terminal.get('release_verified') is True
            and type(save_terminal.get('action_id')) is str
            and save_effect.get('event') == 'effect_checked'
            and save_effect.get('action') == save_action
            and save_effect.get('action_id') == save_terminal['action_id']
            and save_effect.get('status') == 'unavailable'
            and finished.get('event') == 'runtime_finished'
            and finished.get('outcome') == 'SAFE_YIELD'
            and finished.get('reason') == 'effect_unavailable'):
        return None
    request_ns = save_request['save_request_monotonic_ns']
    if (type(save_effect.get('effect_verification_started_ns')) is not int
            or type(save_effect.get('effect_verification_accepted_ns')) is not int
            or not request_ns <= save_effect['effect_verification_started_ns']
                <= save_effect['effect_verification_accepted_ns']):
        return None
    transitions = method_receipt.get('transitions')
    if (type(transitions) is not list or len(transitions) != 2
            or [row.get('action') for row in transitions if type(row) is dict]
                != [entry_action, save_action]
            or any(row.get('release_verified') is not True for row in transitions
                   if type(row) is dict)):
        return None
    digest = hashlib.sha256(json.dumps(method_receipt, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()
    return {'schema': _SAVE_CONTROLLER_SCHEMA, 'call_id': call_id,
        'attempt_id': attempt_id, 'profile_id': 'calc-ocr-save-v1',
        'process_generation': process_generation,
        'window_generation': window_generation,
        'save_request_id': save_request['save_request_id'],
        'save_request_monotonic_ns': request_ns,
        'save_action_id': save_terminal['action_id'],
        'method_receipt_sha256': digest}


class CalcTaskArtifact:
    """Reserve one unique blank FODS and keep its authority in process memory."""

    def __init__(self, call_root, *, call_id, attempt_id, process_generation=None,
                 window_generation=None, target_xid=None, target_pid=None,
                 target_start_ticks=None, expected_values=None, task_plan=None,
                 clock=time.monotonic_ns):
        if type(call_id) is not str or not re.fullmatch(r'[0-9a-f]{32}', call_id):
            raise ValueError('invalid call ID')
        if (type(attempt_id) is not str or not re.fullmatch(r'[\x21-\x7e]{1,128}', attempt_id)):
            raise ValueError('invalid attempt ID')
        identity_values = (target_xid,target_pid,target_start_ticks)
        if (process_generation is None) != (window_generation is None):
            raise ValueError('process and window generations must be bound together')
        if process_generation is None and any(value is not None for value in identity_values):
            raise ValueError('target identity fields require bound generations')
        if process_generation is not None:
            for value in (process_generation, window_generation):
                if type(value) is not str or not re.fullmatch(r'[0-9a-f]{64}', value):
                    raise ValueError('exact process and window generations are required')
            self._validate_target_identity(*identity_values,
                process_generation=process_generation)
        self.call_root = _stable_directory(call_root)
        self.call_id = call_id
        self.attempt_id = attempt_id
        self._expected_values = validate_calc_task_values(expected_values)
        self._task_plan = None
        self._task_plan_sha256 = None
        self._bound_task_plan = None
        if task_plan is not None:
            from .calc_symbolic_plan_v1 import validate_and_bind_calc_plan
            bound = validate_and_bind_calc_plan(task_plan,
                session_scope='prepared-scope', surface='prepared-surface',
                target_aliases={'entry':'prepared_entry','save':'prepared_save'})
            self._task_plan = copy.deepcopy(task_plan)
            self._task_plan_sha256 = bound['plan_sha256']
        self._process_generation = None
        self._window_generation = None
        self._target_xid = None
        self._target_pid = None
        self._target_start_ticks = None
        self.clock = clock
        self.path = self.call_root / _ARTIFACT_NAME
        self._save_request_id = None
        self._save_request_ns = None
        self._verified = None
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_BINARY', 0)
        flags |= getattr(os, 'O_NOFOLLOW', 0)
        fd = os.open(self.path, flags, 0o600)
        try:
            view = memoryview(_BLANK_FODS)
            while view:
                count = os.write(fd, view)
                if count <= 0:
                    raise OSError('short write reserving blank FODS')
                view = view[count:]
            os.fsync(fd)
        finally:
            os.close(fd)
        data, self._blank_identity = _read_regular(self.path, max_bytes=64 * 1024 * 1024)
        if data != _BLANK_FODS:
            raise ValueError('reserved blank artifact changed during admission')
        self._blank_sha256 = hashlib.sha256(data).hexdigest()
        if process_generation is not None:
            self.bind_target(process_generation=process_generation,
                window_generation=window_generation,target_xid=target_xid,
                target_pid=target_pid,target_start_ticks=target_start_ticks)

    @staticmethod
    def _validate_target_identity(xid,pid,start_ticks,*,process_generation):
        from runtime.guarded_x11_v1.process_identity import (
            process_generation_from_identity)
        try:
            computed = process_generation_from_identity(xid,pid,start_ticks)
        except ValueError as error:
            raise ValueError('exact XRes target PID/start-tick identity is required') from error
        if computed != process_generation:
            raise ValueError('target identity fields do not match process generation')

    def bind_target(self, *, process_generation, window_generation,
                    target_xid=None,target_pid=None,target_start_ticks=None):
        """Bind the reserved file once to a freshly identified launch target.

        This split permits reserving the unique file before an owned Calc
        process is launched. Binding fails closed if the reservation changed
        while the process/window identity was being established.
        """
        if (self._process_generation is not None
                or self._window_generation is not None
                or self._save_request_id is not None or self._verified is not None):
            raise ValueError('artifact target is already bound or terminal')
        for value in (process_generation, window_generation):
            if type(value) is not str or not re.fullmatch(r'[0-9a-f]{64}', value):
                raise ValueError('exact process and window generations are required')
        self._validate_target_identity(target_xid,target_pid,target_start_ticks,
            process_generation=process_generation)
        data, identity = _read_regular(self.path, max_bytes=64 * 1024 * 1024)
        if (data != _BLANK_FODS or identity != self._blank_identity
                or hashlib.sha256(data).hexdigest() != self._blank_sha256):
            raise ValueError('reserved blank artifact changed before target binding')
        self._process_generation = process_generation
        self._window_generation = window_generation
        self._target_xid = target_xid
        self._target_pid = target_pid
        self._target_start_ticks = target_start_ticks

    @property
    def process_generation(self):
        return self._process_generation

    @property
    def expected_values(self):
        return dict(self._expected_values)

    @property
    def task_plan(self):
        return copy.deepcopy(self._task_plan)

    @property
    def task_plan_sha256(self):
        return self._task_plan_sha256

    @property
    def bound_task_plan(self):
        return copy.deepcopy(self._bound_task_plan)

    def bind_task_plan(self, *, session_scope, surface, target_aliases):
        """Bind only the retained plan to fresh, caller-minted references."""
        if self._task_plan is None:
            return None
        if self._bound_task_plan is not None:
            raise ValueError('Calc task plan is already bound')
        from .calc_symbolic_plan_v1 import validate_and_bind_calc_plan
        bound = validate_and_bind_calc_plan(self._task_plan,
            session_scope=session_scope, surface=surface,
            target_aliases=target_aliases)
        if bound['plan_sha256'] != self._task_plan_sha256:
            raise ValueError('retained Calc task plan digest changed')
        self._bound_task_plan = copy.deepcopy(bound)
        return copy.deepcopy(bound)

    @property
    def window_generation(self):
        return self._window_generation

    @property
    def descriptor(self):
        """Immutable server-created values suitable for an internal launch request."""
        if self.process_generation is None or self.window_generation is None:
            raise ValueError('artifact target generation is not bound')
        descriptor = {'schema':_DESCRIPTOR_SCHEMA,
                'call_id': self.call_id, 'attempt_id': self.attempt_id,
                'profile_id': 'calc-ocr-save-v1', 'artifact_name': _ARTIFACT_NAME,
                'expected_values': dict(self.expected_values),
                'task_plan_sha256': self.task_plan_sha256,
                'blank_sha256': self._blank_sha256,
                'blank_bytes': len(_BLANK_FODS),
                'blank_identity': list(self._blank_identity),
                'process_generation': self.process_generation,
                'window_generation': self.window_generation}
        descriptor.update(target_xid=self._target_xid,target_pid=self._target_pid,
            target_start_ticks=self._target_start_ticks)
        return descriptor

    def record_save_request(self, *, process_generation, window_generation):
        """Record one fixed-profile save request after a trusted dispatch returns."""
        if (self._save_request_id is not None or self._verified is not None
                or self.process_generation is None or self.window_generation is None
                or process_generation != self.process_generation
                or window_generation != self.window_generation):
            raise ValueError('save request is duplicate, terminal, or target generation changed')
        self._save_request_id = secrets.token_hex(16)
        self._save_request_ns = self.clock()
        self._save_request = {'schema':_SAVE_REQUEST_SCHEMA,
                'call_id':self.call_id,'attempt_id':self.attempt_id,
                'process_generation':self.process_generation,
                'window_generation':self.window_generation,
                'save_request_id': self._save_request_id,
                'save_request_monotonic_ns': self._save_request_ns}
        return dict(self._save_request)

    def verify_after_close(self, close_receipt, target_exit_receipt=None,
                           trusted_save_controller_receipt=None):
        """Score only after both input-owner and exact target process retirement."""
        if self._verified is not None:
            return dict(self._verified)
        if (self.process_generation is None or self.window_generation is None):
            if (not isinstance(close_receipt, dict)
                    or close_receipt.get('status') != 'closed'
                    or close_receipt.get('verified') is not True
                    or close_receipt.get('owner_process_retired') is not True
                    or close_receipt.get('release_confirmed') is not True):
                return {'status':'unknown','task_success':None,
                        'reason':'verified_close_required','replay_allowed':False,
                        'call_id':self.call_id}
            self._verified = {'status':'unknown','task_success':None,
                'reason':'target_generation_unbound','replay_allowed':False,
                'call_id':self.call_id,'attempt_id':self.attempt_id}
            return dict(self._verified)
        result = verify_task_artifact_descriptor(self.call_root,
            descriptor=self.descriptor,
            save_request=getattr(self, '_save_request', None),
            close_receipt=close_receipt,
            target_exit_receipt=target_exit_receipt,
            trusted_save_controller_receipt=trusted_save_controller_receipt)
        if result.get('reason') not in (
                'verified_close_required', 'target_process_exit_required',
                'target_process_exit_invalid', 'target_exit_before_save_request'):
            self._verified = dict(result)
        return result


def verify_task_artifact_descriptor(call_root, *, descriptor, save_request,
                                    close_receipt, target_exit_receipt=None,
                                    trusted_save_controller_receipt=None):
    """Parent-side read-only verifier for child data retained in server memory."""
    try:
        root = _stable_directory(call_root)
    except (OSError, ValueError, TypeError):
        return {'status':'unknown','task_success':None,
                'reason':'call_directory_invalid','replay_allowed':False}
    call_id = root.name
    unknown = {'status': 'unknown', 'task_success': None,
               'replay_allowed': False, 'call_id': call_id}
    if (not isinstance(close_receipt, dict)
            or close_receipt.get('status') != 'closed'
            or close_receipt.get('verified') is not True
            or close_receipt.get('owner_process_retired') is not True
            or close_receipt.get('release_confirmed') is not True):
        return dict(unknown, reason='verified_close_required')
    try:
        expected_values = validate_calc_task_values(
            descriptor.get('expected_values') if type(descriptor) is dict else None)
    except (TypeError, ValueError):
        return dict(unknown, reason='artifact_expected_values_invalid')
    descriptor_fields = {'schema','call_id','attempt_id','profile_id',
        'artifact_name','expected_values','task_plan_sha256',
        'blank_sha256','blank_bytes','blank_identity',
        'process_generation','window_generation','target_xid','target_pid',
        'target_start_ticks'}
    if (type(descriptor) is not dict or set(descriptor) != descriptor_fields
            or descriptor.get('schema') != _DESCRIPTOR_SCHEMA
            or descriptor.get('call_id') != call_id
            or descriptor.get('profile_id') != 'calc-ocr-save-v1'
            or descriptor.get('artifact_name') != _ARTIFACT_NAME
            or descriptor.get('expected_values') != expected_values
            or (descriptor.get('task_plan_sha256') is not None
                and (type(descriptor.get('task_plan_sha256')) is not str
                     or not re.fullmatch(r'[0-9a-f]{64}',
                                         descriptor['task_plan_sha256'])))
            or type(descriptor.get('attempt_id')) is not str
            or not re.fullmatch(r'[\x21-\x7e]{1,128}',descriptor['attempt_id'])
            or type(descriptor.get('blank_sha256')) is not str
            or not re.fullmatch(r'[0-9a-f]{64}',descriptor['blank_sha256'])
            or descriptor.get('blank_bytes') != len(_BLANK_FODS)
            or descriptor.get('blank_sha256') != hashlib.sha256(_BLANK_FODS).hexdigest()
            or type(descriptor.get('blank_identity')) is not list
            or len(descriptor['blank_identity']) != 5
            or any(type(value) is not int or value < 0
                   for value in descriptor['blank_identity'])
            or any(type(descriptor.get(name)) is not str
                   or not re.fullmatch(r'[0-9a-f]{64}',descriptor[name])
                   for name in ('process_generation','window_generation'))):
        return dict(unknown, reason='artifact_descriptor_invalid')
    try:
        CalcTaskArtifact._validate_target_identity(
            descriptor['target_xid'],descriptor['target_pid'],
            descriptor['target_start_ticks'],
            process_generation=descriptor['process_generation'])
    except (KeyError,TypeError,ValueError):
        return dict(unknown,reason='artifact_target_identity_invalid')
    if not isinstance(target_exit_receipt, dict):
        return dict(unknown, reason='target_process_exit_required',
                    attempt_id=descriptor['attempt_id'])
    exit_common = {'status','verified','process_generation','xid','pid',
                   'start_ticks','exit_code','observed_monotonic_ns'}
    direct_exit_fields = exit_common | {'schema'}
    wrapped_exit_fields = exit_common | {
        'schema','custody','launcher_pid','launcher_start_ticks',
        'launcher_executable','launcher_package_version','launcher_exit_code',
        'replacement_observed'}
    schema = target_exit_receipt.get('schema')
    if schema == 'agent-interface/calc-target-exit-receipt-v1':
        exit_receipt_shape_valid = set(target_exit_receipt) == direct_exit_fields
    elif schema == 'agent-interface/calc-target-exit-receipt-v2':
        exit_receipt_shape_valid = (
            set(target_exit_receipt) == wrapped_exit_fields
            and target_exit_receipt.get('custody')
                == 'libreoffice-oosplash-direct-child-v1'
            and type(target_exit_receipt.get('launcher_pid')) is int
            and target_exit_receipt['launcher_pid'] > 0
            and target_exit_receipt.get('launcher_pid') != target_exit_receipt.get('pid')
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
        exit_receipt_shape_valid = False
    if (not exit_receipt_shape_valid
            or target_exit_receipt.get('status') != 'exited'
            or target_exit_receipt.get('verified') is not True
            or target_exit_receipt.get('process_generation')
                != descriptor['process_generation']
            or target_exit_receipt.get('xid') != descriptor['target_xid']
            or target_exit_receipt.get('pid') != descriptor['target_pid']
            or target_exit_receipt.get('start_ticks')
                != descriptor['target_start_ticks']
            or type(target_exit_receipt.get('pid')) is not int
            or target_exit_receipt['pid'] <= 0
            or type(target_exit_receipt.get('start_ticks')) is not int
            or target_exit_receipt['start_ticks'] <= 0
            or type(target_exit_receipt.get('exit_code')) is not int
            or target_exit_receipt['exit_code'] != 0
            or type(target_exit_receipt.get('observed_monotonic_ns')) is not int
            or target_exit_receipt['observed_monotonic_ns'] <= 0):
        return dict(unknown, reason='target_process_exit_invalid',
                    attempt_id=descriptor['attempt_id'])
    save_fields = {'schema','call_id','attempt_id','process_generation',
        'window_generation','save_request_id','save_request_monotonic_ns'}
    if (type(save_request) is not dict or set(save_request) != save_fields
            or save_request.get('schema') != _SAVE_REQUEST_SCHEMA
            or save_request.get('call_id') != call_id
            or save_request.get('attempt_id') != descriptor['attempt_id']
            or save_request.get('process_generation') != descriptor['process_generation']
            or save_request.get('window_generation') != descriptor['window_generation']
            or type(save_request.get('save_request_id')) is not str
            or not re.fullmatch(r'[0-9a-f]{32}',save_request['save_request_id'])
            or type(save_request.get('save_request_monotonic_ns')) is not int
            or save_request['save_request_monotonic_ns'] <= 0):
        return dict(unknown, reason='trusted_save_request_unavailable')
    if (target_exit_receipt['observed_monotonic_ns']
            <= save_request['save_request_monotonic_ns']):
        return dict(unknown, reason='target_exit_before_save_request',
                    attempt_id=descriptor['attempt_id'])
    try:
        data, identity = _read_regular(root / _ARTIFACT_NAME,
                                       max_bytes=64 * 1024 * 1024)
    except (OSError, ValueError, TypeError):
        return dict(unknown, reason='artifact_missing_or_unstable')
    digest = hashlib.sha256(data).hexdigest()
    if (digest == descriptor['blank_sha256']
            or identity == tuple(descriptor['blank_identity'])):
        return dict(unknown, reason='artifact_unchanged_after_save_request',
                    attempt_id=descriptor['attempt_id'],
                    artifact_sha256=digest,artifact_identity=list(identity))
    effect = verify_saved_fods_bytes(data, expected=descriptor['expected_values'])
    result_fields = dict(attempt_id=descriptor['attempt_id'],
        profile_id='calc-ocr-save-v1',
        expected_values=dict(descriptor['expected_values']),
        process_generation=descriptor['process_generation'],
        window_generation=descriptor['window_generation'],
        save_request_id=save_request['save_request_id'],
        save_request_monotonic_ns=save_request['save_request_monotonic_ns'],
        blank_sha256=descriptor['blank_sha256'],artifact_sha256=digest,
        artifact_bytes=len(data),artifact_identity=list(identity),parsed_effect=effect)
    if effect.get('status') != 'verified' or effect.get('task_success') is not True:
        return dict(unknown, reason='saved_artifact_not_scored', **result_fields)
    controller_fields = {'schema','call_id','attempt_id','profile_id',
        'process_generation','window_generation','save_request_id',
        'save_request_monotonic_ns','save_action_id','method_receipt_sha256'}
    controller = trusted_save_controller_receipt
    if (type(controller) is not dict or set(controller) != controller_fields
            or controller.get('schema') != _SAVE_CONTROLLER_SCHEMA
            or controller.get('call_id') != descriptor['call_id']
            or controller.get('attempt_id') != descriptor['attempt_id']
            or controller.get('profile_id') != 'calc-ocr-save-v1'
            or controller.get('process_generation') != descriptor['process_generation']
            or controller.get('window_generation') != descriptor['window_generation']
            or controller.get('save_request_id') != save_request['save_request_id']
            or controller.get('save_request_monotonic_ns')
                != save_request['save_request_monotonic_ns']
            or type(controller.get('save_action_id')) is not str
            or not re.fullmatch(r'action-[0-9a-f]{32}', controller['save_action_id'])
            or type(controller.get('method_receipt_sha256')) is not str
            or not re.fullmatch(r'[0-9a-f]{64}', controller['method_receipt_sha256'])):
        return dict(unknown, reason='trusted_save_controller_unavailable', **result_fields)
    return {'status':'verified','task_success':True,'replay_allowed':False,
        'reason':'registered_calc_saved_artifact_verified',**result_fields,
        'save_controller':dict(controller)}
