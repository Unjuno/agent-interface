"""Optional stdio MCP transport; one-shot by default, with explicit owned-session modes."""
import argparse
import asyncio
from concurrent.futures import ThreadPoolExecutor
import contextvars
from copy import deepcopy
from contextlib import asynccontextmanager
import json
from itertools import islice, dropwhile
import math
import os
from pathlib import Path
import threading
import time
from typing import Annotated, Literal
import uuid

from mcp.server.fastmcp import FastMCP
import anyio
from mcp.types import CallToolResult, ImageContent, TextContent
from pydantic import Field, StrictBool, StrictInt, StrictStr, ValidationError

from .api import dispatch
from .mcp_session import MCPSessionOwner
from .attempt import _write_json
from .observe import observe, observe_in_session
from .review import present_result
from .validate_program import SCHEMA as VALIDATION_SCHEMA, inspect_program

# Reserve time to resume the loop and encode a response within the caller budget.
_GUARDED_CANCEL_CALLER_RESPONSE_BUDGET_NS = 300_000_000
_GUARDED_CANCEL_RESPONSE_HANDOFF_MARGIN_NS = 50_000_000
_GUARDED_CANCEL_TRANSACTION_TIMEOUT_S = 4.0
_SUPERVISED_WIN32_CLEANUP_NS = 3_000_000_000
_SUPERVISED_WIN32_COMPLETION_OBSERVER_NS = 1_000_000_000
_SUPERVISED_WIN32_DEADLINE_POLL_MAX_S = 0.002


def _x11_root_window_id(display_name=None):
    """Return the root XID for the configured connection without changing focus."""
    from Xlib import display as xdisplay
    connection=xdisplay.Display(display_name)
    try:
        return connection.screen().root.id
    finally:
        connection.close()


def _normalize_supervised_win32_program(program):
    """Apply the standard caller's bounded syntax expansion before admission."""
    if type(program) is not dict or type(program.get('ops')) is not list:
        raise ValueError('PROGRAM_NOT_OBJECT')
    from runtime.core_v1.sequence import normalize_observation_regions
    operations, region_indices = normalize_observation_regions(program['ops'])
    normalized = deepcopy(program)
    normalized['ops'] = operations
    compilation = None
    if any(isinstance(op, dict) and 'gap_ms' in op for op in operations):
        from runtime.core_v1.sequence import expand_text_gaps
        expanded, sources = expand_text_gaps(operations)
        compilation = {'kind': 'bounded_text_gap',
                       'source_program': deepcopy(normalized),
                       'operation_sources': sources}
        normalized['ops'] = expanded
    elif any(isinstance(op, dict) and 'repeat' in op for op in operations):
        from runtime.core_v1.sequence import expand_key_repeats
        expanded = expand_key_repeats(operations, max_ops=128)
        compilation = {'kind': 'bounded_key_repeat',
                       'source_program': deepcopy(normalized),
                       'operation_sources': [index for index, op in enumerate(operations)
                           for _ in range(op.get('repeat', 1))]}
        normalized['ops'] = expanded
    normalization = ({'kind': 'explicit_observation_region',
        'source_program': deepcopy(program), 'source_operation_indices': region_indices}
        if region_indices else None)
    return normalized, normalization, compilation


def _run_supervised_win32_dispatch(owner, producer_factory, call_id, arguments,
                                   cancel_requested=lambda: False):
    """Run one standard program through native producer and custody receipts."""
    from copy import deepcopy
    program, normalization, compilation = _normalize_supervised_win32_program(
        arguments['program'])
    read_result = getattr(producer_factory, 'read_result', None)
    if not callable(read_result):
        raise ValueError('NATIVE_PRODUCER_RESULT_READER_REQUIRED')
    authority = program.get('authority')
    if type(authority) is not dict or type(authority.get('expires_at_ns')) is not int:
        raise ValueError('INVALID_AUTHORITY_DEADLINE')
    operation_id = uuid.uuid4().hex
    binding = owner.bind_target_generation()
    owner.admit_standard_action(call_id, operation_id,
        binding['target_binding_id'], program,
        operation_deadline_ns=authority['expires_at_ns'],
        current_observation_seq=arguments['current_observation_seq'],
        current_binding_revision=arguments['current_binding_revision'])
    if cancel_requested():
        owner.cancel_guarded(call_id,
            cleanup_deadline_ns=time.monotonic_ns() + _SUPERVISED_WIN32_CLEANUP_NS)
        row = owner.interface_result(call_id)
        return {'schema': 'agent-interface/runtime-dispatch-result-v1',
            'status': 'returned', 'result': {'status': 'cancel_pending',
                'input_dispatched': False, 'task_success': None,
                'replay_allowed': False}, 'supervision': row,
            'target_generation': binding['target_generation'],
            'operation_id': operation_id, 'call_id': call_id,
            'operation_invoked': False, 'input_dispatched': False,
            'release_confirmed': False, 'task_success': None,
            'replay_allowed': False}
    owner.start_producer(call_id, producer_factory)
    deadline_ns = authority['expires_at_ns']
    while True:
        row = owner.complete_exited_action(call_id, result_reader=read_result,
            readback_reader=lambda request: owner.observe_completed_producer(
                request['operation_id'], request['target_generation'],
                producer_exit_confirmed_ns=request['producer_exit_confirmed_ns'],
                deadline_ns=max(deadline_ns,
                    time.monotonic_ns() + _SUPERVISED_WIN32_COMPLETION_OBSERVER_NS)))
        action = row['action']
        cancellation = row.get('cancellation')
        if (action.get('status') != 'running'
                or (isinstance(cancellation, dict)
                    and cancellation.get('status') in ('recovered', 'unknown'))):
            break
        now_ns = time.monotonic_ns()
        if now_ns >= deadline_ns:
            owner.cancel_guarded(call_id,
                cleanup_deadline_ns=now_ns + _SUPERVISED_WIN32_CLEANUP_NS)
            row = owner.interface_result(call_id)
            break
        # Keep the cancellation monitor responsive near lease expiry. Windows
        # monotonic_ns may still advance at the system-timer cadence, so this
        # reduces avoidable sleep latency but is not a hard real-time bound.
        time.sleep(min(_SUPERVISED_WIN32_DEADLINE_POLL_MAX_S,
            (deadline_ns - now_ns) / 1_000_000_000))
    action = row['action']
    cancellation = row.get('cancellation')
    if (action.get('status') in ('running', 'cancel_pending')
            and isinstance(cancellation, dict)
            and cancellation.get('status') == 'unknown'):
        # This dispatch worker is returning without an action receipt. Retain
        # that terminal uncertainty on the action record while leaving owner
        # custody UNKNOWN; cancellation status alone must not imply release.
        row = owner.record_action_result(call_id, {
            'status': 'unknown', 'input_dispatched': None,
            'release_confirmed': False, 'effect_status': 'unknown',
            'task_success': None, 'replay_allowed': False})
        action = row['action']
    elif (isinstance(cancellation, dict)
            and cancellation.get('automatic_completion_recovery') is True
            and cancellation.get('status') == 'recovered'):
        # Release confirmation is carried by the separate cancellation
        # transaction. The failed producer's action itself stays UNKNOWN.
        row = owner.record_action_result(call_id, {
            'status': 'unknown', 'input_dispatched': None,
            'release_confirmed': False,
            'error': 'COMPLETION_EVIDENCE_UNCONFIRMED',
            'error_type': cancellation.get('completion_error_type'),
            'effect_status': 'unknown', 'task_success': None,
            'replay_allowed': False})
        action = row['action']
    elif (action.get('status') in ('running', 'cancel_pending')
            and isinstance(cancellation, dict)
            and cancellation.get('status') == 'recovered'):
        # A verified recovery ends the dispatch worker too. Persist that
        # terminal action receipt separately from the cancellation receipt;
        # task effect and input-dispatched state remain unknown after cancel.
        custody = cancellation.get('result')
        confirmed = (cancellation.get('release_confirmed') is True
            and cancellation.get('action_operation_id') == action.get('operation_id')
            and cancellation.get('target_generation') == action.get('target_generation')
            and isinstance(custody, dict)
            and custody.get('operation_id') == action.get('operation_id')
            and custody.get('target_generation') == action.get('target_generation')
            and custody.get('phase') == 'recovered'
            and custody.get('status') == 'recovered'
            and custody.get('release_confirmed') is True)
        row = owner.record_action_result(call_id, {
            'status': 'recovered' if confirmed else 'unknown',
            'input_dispatched': None,
            'release_confirmed': confirmed,
            'obligations': (list(custody.get('obligations', []))
                if isinstance(custody, dict)
                and isinstance(custody.get('obligations'), list) else []),
            'effect_status': 'unknown', 'task_success': None,
            'replay_allowed': False})
        action = row['action']
    progress_reader = getattr(
        producer_factory, 'read_program_actions_lower_bound', None)
    if (callable(progress_reader)
            and action.get('status') in ('recovered', 'unknown')):
        try:
            row = owner.capture_program_emission_progress(call_id,
                progress_reader)
            action = row['action']
        except Exception as error:
            # Recovery custody remains authoritative. Missing progress evidence
            # leaves delivery unknown; it must not undo a verified release.
            try:
                row = owner.record_program_emission_progress_failure(
                    call_id, error)
                action = row['action']
            except Exception:
                pass
    elif action.get('status') in ('recovered', 'unknown'):
        try:
            row = owner.record_program_emission_progress_failure(call_id,
                RuntimeError('progress_reader_unavailable'))
            action = row['action']
        except Exception:
            pass
    if action.get('status') in ('recovered', 'unknown'):
        row = owner.interface_result(call_id)
        action = row['action']
    result = action.get('result') or {'status': action.get('status', 'unknown'),
        'task_success': None, 'replay_allowed': False}
    cancellation = row.get('cancellation')
    release_confirmed = action.get('release_confirmed') is True
    if isinstance(cancellation, dict):
        release_confirmed = release_confirmed or cancellation.get('release_confirmed') is True
    execution = result.get('execution') if type(result) is dict else None
    program_emissions = (execution.get('program_emissions')
        if type(execution) is dict else None)
    if type(program_emissions) is not int and type(result) is dict:
        program_emissions = result.get('program_emissions')
    if type(program_emissions) is int:
        input_dispatched = program_emissions > 0
    elif type(result.get('input_dispatched')) is bool:
        input_dispatched = result['input_dispatched']
    else:
        emissions = execution.get('emissions') if type(execution) is dict else None
        input_dispatched = emissions > 0 if type(emissions) is int else None
    return {'schema': 'agent-interface/runtime-dispatch-result-v1',
        'status': 'returned', 'result': deepcopy(result),
        'normalization': normalization, 'compilation': compilation,
        'supervision': row, 'target_generation': action['target_generation'],
        'operation_id': operation_id, 'call_id': call_id,
        'operation_invoked': True,
        'input_dispatched': input_dispatched,
        'release_confirmed': release_confirmed,
        'task_success': None, 'replay_allowed': False}


# Documentation metadata only: the public compiler and core remain the validators.
# Keep dict forwarding intact, including extensions and malformed-request receipts.
PublicProgram = Annotated[dict, Field(description=(
    'Bounded agent-interface/program-v1 object. Required fields: '
    'schema="agent-interface/program-v1", program_id (1..64 letters/digits/._-), '
    'source={observation_seq: integer, binding_revision: integer, target_generations?: {configured_target: sha256}}, '
    'authority={lease_id: identifier, expires_at_ns: integer in the execution host monotonic clock}, '
    'terminal={release_all_required: true}, and ops (ordered objects). '
    'The caller must supply a valid current lease and matching source/binding assertions; '
    'this server does not mint them. Begin with {"op":"focus","target":"configured-name"} '
    'when input requires focus. On X11, each program containing pointer_move or observe '
    'must put focus or activate before those operations; a previous dispatch or '
    'interface_observe does not supply that program-local target. '
    'For Win32, interface_observe returns target_generation; include it under '
    'source.target_generations for every target focused by this program. The standard '
    'caller rechecks those generations before dispatch and refuses missing or changed '
    'values. This is a pre-dispatch check, not an atomic window-lifetime fence. '
    'Focus does not '
    'acknowledge widget readiness or text delivery. '
    'Operation examples: {"op":"text","text":"abc","gap_ms":20}, '
    '{"op":"key_chord","keys":["Left"],"repeat":2}, '
    '{"op":"key_chord","keys":["CTRL","s"]}, '
    '{"op":"observe","frame":"window_client","region":[0,0,400,180]}. '
    'For a drag, use pointer_move with frame/x/y, pointer_button with button=left/down=true, '
    'pointer_move to the observed destination, then pointer_button with button=left/down=false. '
    'For example: {"op":"pointer_button","button":"left","down":true}. '
    'These are sequential operations on one pointer, not concurrent cursors. '
    'Batch only steps whose next action does not need another model decision; '
    'return an observation at that decision boundary. '
    'Observe region uses [x,y,width,height], just like interface_observe. '
    'Legacy x/y/w/h fields remain supported; do not mix them with region. '
    'Use the actual target and observed region; examples do not select them for you. '
    'End with exactly one {"op":"release_all"}. Expanded ops must fit 128. '
    'gap_ms is optional integer 0..1000; key_chord repeat is optional integer 1..126. '
    'Observation captures once and does not pause for a model decision. '
    'Before replacing field text, inspect the selection and resulting value before committing. '
    'Emitted clicks or CTRL+a are not acknowledgements that a widget has processed them. '
    'On X11, window_client uses target-client coordinates and may omit overlapping dialogs; '
    'screen_physical_px uses display coordinates and includes other visible windows in the explicit region. '
    'X11 key names are case-sensitive: use Home, End, Left, Right, Up, Down, '
    'BackSpace, Delete or Insert; supported aliases include CTRL, SHIFT, ALT, ENTER, TAB, ESC, SPACE. '
    'Use key_chord with keys for a tap/chord, or key_state with key/down for held input; '
    'there is no key operation. Key mapping is checked on the execution host. '
    'wait_update with timeout_ms is a fixed delay on X11, not a redraw acknowledgement.'
))]


def content(result, *, error=False, include_image=True):
    metadata = dict(result)
    image = metadata.pop('image', None)
    if image is not None and not include_image:
        metadata['image_delivery'] = 'omitted_by_request'
    blocks = [TextContent(type='text', text=json.dumps(metadata, allow_nan=False))]
    if image is not None and include_image:
        blocks.append(ImageContent(**image))
    return CallToolResult(content=blocks, isError=error)



class PublicArgumentMCP(FastMCP):
    """Reject malformed public arguments before tool invocation or input.

    The registered FastMCP argument model is prevalidated so schema failures are
    distinguishable from errors raised by the tool function itself. This reads
    FastMCP's tool metadata but does not modify it; normal calls still use the
    public ``call_tool`` path.
    """
    async def list_tools(self):
        tools = await super().list_tools()
        return [tool.model_copy(update={
            'inputSchema': {**tool.inputSchema, 'additionalProperties': False}
        }) for tool in tools]

    async def call_tool(self, name, arguments):
        for tool in await self.list_tools():
            if tool.name == name:
                schema = tool.inputSchema
                properties = schema.get('properties', {})
                unknown = sorted(set(arguments) - set(properties))
                if unknown:
                    return content({'status': 'invalid_request',
                        'error': 'unknown top-level tool arguments',
                        'unknown_arguments': unknown, 'operation_invoked': False,
                        'input_dispatched': False, 'replay_allowed': False}, error=True)
                missing = sorted(set(schema.get('required', ())) - set(arguments))
                if missing:
                    return content({'status': 'invalid_request',
                        'error': 'missing required tool arguments',
                        'missing_arguments': missing, 'operation_invoked': False,
                        'input_dispatched': False, 'release_confirmed': None,
                        'effect_status': 'unknown', 'task_success': None,
                        'replay_allowed': False}, error=True)
                registered_tool = self._tool_manager.get_tool(name)
                metadata = registered_tool.fn_metadata
                try:
                    parsed = metadata.pre_parse_json(arguments)
                    validated = metadata.arg_model.model_validate(parsed)
                    validated.model_dump_one_level()
                except ValidationError as error:
                    errors = error.errors(include_input=False)
                    details = []
                    for item in errors[:32]:
                        path = [part for part in item.get('loc', ())
                                if type(part) in (str, int)]
                        code = item.get('type')
                        details.append({'path': path,
                                        'code': code if isinstance(code, str)
                                        else 'validation_error'})
                    return content({'status': 'invalid_request',
                        'error': 'tool arguments failed schema validation',
                        'validation_errors': details,
                        'validation_errors_truncated': len(errors) > len(details),
                        'operation_invoked': False, 'input_dispatched': False,
                        'release_confirmed': None, 'effect_status': 'unknown',
                        'task_success': None, 'replay_allowed': False}, error=True)
                break
        return await super().call_tool(name, arguments)


def present_management_report(report, call_root, *, include_image=True):
    row = dict(report)
    if 'observation_report' in report:
        # Keep the raw capture and committed selection, but do not present an
        # image whose target association failed or could not be rechecked.
        # This gate also applies to retained lookup without renewing evidence.
        inconsistent = (
            (report.get('status') == 'needs_review' and report.get('error') is not None)
            or ('capture_consistency' in report and report['capture_consistency'] != 'matched'))
        if inconsistent:
            row.update(image=None, image_status='needs_review',
                       image_error='Target/capture association unconfirmed; inspect again before new input.')
            return row
        shown = present_result(report['observation_report'], call_root, include_image=include_image)
        for key in ('image', 'image_status', 'image_error', 'image_delivery'):
            if key in shown:
                row[key] = shown[key]
    return row


class _WorkerAdmission:
    """Transfer a slot to one worker, or revoke it before any invocation."""
    def __init__(self, slot, completed):
        self.slot = slot
        self.completed = completed
        self.guard = threading.Lock()
        self.state = 'pending'

    def enter(self):
        with self.guard:
            if self.state != 'pending':
                return False
            self.state = 'running'
            return True

    def revoke_pending(self):
        with self.guard:
            if self.state != 'pending':
                return False
            self.state = 'revoked'
            self.slot.release()
        self.completed()
        return True

    def finish(self):
        with self.guard:
            self.state = 'finished'
            self.slot.release()
        self.completed()


def create_server(targets, output_directory, *, display_name=None, session_mode="one-shot",
                  guarded_process_identity=False, guarded_query_worker=False, guarded_observation_worker=False,
                  guarded_window_lifecycle=False, guarded_owned_process=False,
                  guarded_retention_mode='files',
                  guarded_prestarted_cancel_supervisor=False,
                  _guarded_cancel_supervisor_target=None,
                  _guarded_cancel_transaction_timeout_s=(
                      _GUARDED_CANCEL_TRANSACTION_TIMEOUT_S),
                  _guarded_owner_factory=None,
                  _calc_preparation_ttl_ns=300_000_000_000,
                  _calc_launch_factory=None,
                  _calc_launch_title_hint='task-artifact.fods',
                  _calc_discovery_deadline_s=20.0,
                  _guarded_win32_owner_factory=None,
                  _guarded_win32_producer_factory=None,
                  _guarded_win32_task_oracle=None,
                  _supervised_win32_owner_factory=None,
                  _supervised_win32_producer_factory=None,
                  _supervised_win32_task_oracle=None,
                  supervised_win32_task_oracle=None,
                  supervised_win32_late_input_horizon_ns=0):
    if session_mode not in ("one-shot", "persistent-x11", "guarded-x11",
                            "guarded-win32", "supervised-win32"):
        raise ValueError("unknown session mode")
    guarded_win32 = session_mode == 'guarded-win32'
    supervised_win32 = session_mode == 'supervised-win32'
    if (type(supervised_win32_late_input_horizon_ns) is not int
            or supervised_win32_late_input_horizon_ns < 0
            or (supervised_win32_late_input_horizon_ns and not supervised_win32)):
        raise ValueError('late-input horizon must be a nonnegative integer for supervised-win32')
    if supervised_win32:
        from runtime.guarded_win32_v1.process_cancellation import MAX_LATE_INPUT_HORIZON_NS
        if supervised_win32_late_input_horizon_ns > MAX_LATE_INPUT_HORIZON_NS:
            raise ValueError('late-input horizon exceeds the supervisor maximum')
    if (_supervised_win32_task_oracle is not None
            and supervised_win32_task_oracle is not None):
        raise ValueError('configure only one supervised Win32 task oracle')
    task_oracle = (supervised_win32_task_oracle
                   if supervised_win32_task_oracle is not None
                   else _supervised_win32_task_oracle)
    if (task_oracle is not None
            and (not supervised_win32 or not callable(task_oracle))):
        raise ValueError('supervised Win32 task oracle must be a callable configured for supervised-win32')
    if guarded_win32 and os.name != 'nt':
        raise ValueError('guarded-win32 requires a Windows host')
    if guarded_win32 and (not isinstance(targets, dict) or len(targets) != 1):
        raise ValueError('guarded-win32 requires exactly one explicitly configured target')
    if guarded_win32 and not callable(_guarded_win32_owner_factory):
        raise ValueError('guarded-win32 requires an explicit injected owner factory')
    if guarded_win32 and not callable(_guarded_win32_producer_factory):
        raise ValueError('guarded-win32 requires an explicit gated synthetic producer factory')
    if supervised_win32 and os.name != 'nt':
        raise ValueError('supervised-win32 requires a Windows host')
    if supervised_win32 and (not isinstance(targets, dict) or len(targets) != 1):
        raise ValueError('supervised-win32 requires exactly one explicitly configured target')
    if supervised_win32 and ((_supervised_win32_owner_factory is None)
            != (_supervised_win32_producer_factory is None)):
        raise ValueError('supervised-win32 test factories must be injected as a pair')
    if type(guarded_process_identity) is not bool:
        raise ValueError('guarded_process_identity must be a boolean')
    if guarded_process_identity and session_mode != 'guarded-x11':
        raise ValueError('process identity requires guarded-x11 mode')
    if (type(guarded_query_worker) is not bool
            or (guarded_query_worker and (session_mode != 'guarded-x11' or not guarded_process_identity))):
        raise ValueError('query worker requires guarded-x11 with explicit process identity')
    if (type(guarded_observation_worker) is not bool
            or (guarded_observation_worker and not guarded_query_worker)):
        raise ValueError('observation worker requires explicit guarded query worker')
    if (type(guarded_window_lifecycle) is not bool
            or (guarded_window_lifecycle and not guarded_query_worker)):
        raise ValueError('window lifecycle requires explicit guarded query worker')
    if guarded_retention_mode not in ('files', 'journal'):
        raise ValueError("guarded_retention_mode must be 'files' or 'journal'")
    if guarded_retention_mode != 'files' and session_mode != 'guarded-x11':
        raise ValueError('journal retention requires guarded-x11 mode')
    if (not isinstance(targets, dict) or not targets or
            any(not isinstance(k, str) or not k or type(v) is not int or v <= 0
                for k, v in targets.items())):
        raise ValueError('explicit nonempty target name -> positive native ID mapping required')
    if type(guarded_owned_process) is not bool:
        raise ValueError('guarded_owned_process must be a boolean')
    if (type(guarded_prestarted_cancel_supervisor) is not bool
            or (guarded_prestarted_cancel_supervisor
                and not guarded_owned_process)):
        raise ValueError('prestarted cancellation supervisor requires guarded owned-process mode')
    if (type(_guarded_cancel_transaction_timeout_s) not in (int, float)
            or not math.isfinite(_guarded_cancel_transaction_timeout_s)
            or _guarded_cancel_transaction_timeout_s <= 0):
        raise ValueError('guarded cancellation transaction timeout must be positive')
    if type(_calc_preparation_ttl_ns) is not int or _calc_preparation_ttl_ns <= 0:
        raise ValueError('Calc preparation TTL must be a positive integer nanosecond value')
    if _calc_launch_factory is not None:
        if (not callable(_calc_launch_factory) or os.name != 'posix'
                or session_mode != 'guarded-x11' or not guarded_owned_process
                or not guarded_process_identity or not guarded_query_worker
                or not guarded_window_lifecycle or len(targets) != 1):
            raise ValueError('Calc launch requires POSIX guarded-owned X11 with process identity, query worker, window lifecycle, and one root target')
        if (type(_calc_launch_title_hint) is not str or not _calc_launch_title_hint
                or len(_calc_launch_title_hint)>128
                or not _calc_launch_title_hint.isprintable()
                or type(_calc_discovery_deadline_s) not in (int,float)
                or not math.isfinite(_calc_discovery_deadline_s)
                or not 0 < _calc_discovery_deadline_s <= 60):
            raise ValueError('Calc launch discovery configuration is invalid')
        root_xid=_x11_root_window_id(display_name)
        if next(iter(targets.values())) != root_xid:
            raise ValueError('Calc launch mode requires the configured target to be this X11 root window')
    if guarded_owned_process and (session_mode != 'guarded-x11'
            or not guarded_process_identity or not guarded_query_worker):
        raise ValueError('guarded owned process requires guarded-x11, process identity and query worker')
    targets = deepcopy(targets)
    root = Path(output_directory).resolve()
    root.mkdir(parents=True, exist_ok=True)
    lock = threading.Lock()
    workers = set()
    task_oracle_tasks = set()
    calls = {}
    calls_lock = threading.Lock()
    calc_artifacts = {}
    calc_launches = {}
    calc_preparation_slot = None
    calc_preparation_deadline_ns = None
    supervised_cancel_requests = set()
    cancellation_executor = (ThreadPoolExecutor(max_workers=1,
        thread_name_prefix='guarded-cancel') if guarded_owned_process else None)
    cancellation_futures = {}
    active_cancellation_operation = None
    unarchived_cancellation_call_id = None

    def _supervised_cancel_requested(call_id):
        with calls_lock:
            return call_id in supervised_cancel_requests

    async def load_cancellation_record(call_id, call_record):
        cancellation = call_record.get('cancellation')
        if isinstance(cancellation, dict):
            return deepcopy(cancellation)
        if call_record.get('cancellation_archived') is not True:
            return None
        path = root / call_id / 'cancellation.json'
        try:
            cancellation = json.loads(await asyncio.to_thread(
                path.read_text, encoding='utf-8'))
        except (OSError, ValueError, TypeError):
            cancellation = None
        if (not isinstance(cancellation, dict)
                or cancellation.get('operation_id')
                    != call_record.get('cancellation_operation_id')):
            return {
                'operation_id':call_record.get('cancellation_operation_id'),
                'status':'unknown',
                'persistence_failure':'terminal cancellation receipt unavailable',
                'result':{'status':'cancel_unconfirmed',
                    'release_confirmed':False, 'cleanup_status':'UNKNOWN',
                    'task_success':None, 'replay_allowed':False}}
        return cancellation
    if cancellation_executor is not None:
        # Pay thread startup before the first safety-sensitive cancellation.
        cancellation_executor.submit(lambda: None).result(timeout=5)
    owner = MCPSessionOwner(targets, display_name) if session_mode == 'persistent-x11' else None
    guarded = session_mode == 'guarded-x11'
    if guarded_win32:
        owner = _guarded_win32_owner_factory(deepcopy(targets), root, display_name)
        required_win32 = ('current_target_generation', 'bind_target_generation',
                          'admit_action_from_binding', 'start_producer',
                          'cancel_guarded', 'interface_result', 'list_results', 'close',
                          'begin_task_effect_verification', 'record_task_effect',
                          'fail_task_effect_verification')
        if any(not callable(getattr(owner, name, None)) for name in required_win32):
            raise ValueError('guarded-win32 owner factory returned an incomplete synthetic owner')
        if (getattr(owner, 'mode', None) != 'guarded-win32'
                or getattr(owner, 'synthetic_only', None) is not True):
            raise ValueError('guarded-win32 requires the inert synthetic operation owner')
    elif supervised_win32:
        producer_root = root / 'supervised-win32-producers'
        if callable(_supervised_win32_owner_factory):
            owner = _supervised_win32_owner_factory(
                deepcopy(targets), root, display_name)
            supervised_win32_producer_factory = _supervised_win32_producer_factory(
                deepcopy(targets), producer_root, display_name)
        else:
            from .win32_supervisor_helpers import create_native_win32_components
            owner, supervised_win32_producer_factory = create_native_win32_components(
                deepcopy(targets), producer_root,
                late_input_horizon_ns=supervised_win32_late_input_horizon_ns)
        if supervised_win32_late_input_horizon_ns:
            supervisor = getattr(owner, '_supervisor', None)
            if getattr(supervisor, 'late_input_horizon_ns', None) != supervised_win32_late_input_horizon_ns:
                raise ValueError('supervised Win32 owner did not install the requested late-input horizon')
        required = ('bind_target_generation', 'admit_standard_action',
                    'start_producer', 'complete_exited_action', 'cancel_guarded',
                    'interface_result', 'list_results', 'close')
        if (any(not callable(getattr(owner, name, None)) for name in required)
                or getattr(owner, 'mode', None) != 'supervised-win32'
                or getattr(owner, 'synthetic_only', None) is not False
                or not callable(supervised_win32_producer_factory)
                or not callable(getattr(supervised_win32_producer_factory,
                                        'read_result', None))):
            raise ValueError('supervised-win32 components are incomplete')
    if guarded:
        from .mcp_guarded import GuardedSessionOwner
        owner_options = dict(process_identity=guarded_process_identity,
                             query_worker=guarded_query_worker,
                             observation_worker=guarded_observation_worker,
                             window_lifecycle=guarded_window_lifecycle,
                             retention_mode=guarded_retention_mode)
        if guarded_owned_process:
            from .owned_guarded_session import OwnedGuardedSessionOwner
            owner = OwnedGuardedSessionOwner(targets, root, display_name,
                **owner_options,
                prestarted_cancel_supervisor=guarded_prestarted_cancel_supervisor,
                _cleanup_supervisor_target=_guarded_cancel_supervisor_target,
                _owner_factory=_guarded_owner_factory)
        else:
            owner = GuardedSessionOwner(targets, root, display_name, **owner_options)
    shutting_down = False
    server_shutdown_started = False
    server_instance_id = uuid.uuid4().hex

    def rollback_unentered_close(operation, revoked):
        """Release a manual close reservation only if no worker entered it."""
        nonlocal shutting_down
        if operation != 'close' or not revoked:
            return
        with calls_lock:
            if (not server_shutdown_started
                    and (owner is None or owner.state != 'closed')):
                shutting_down = False

    def close_owner():
        try:
            calc_lifecycle=[]
            clean_exits={}
            try:
                # Close/release the input owner before waiting for the target.
                # The parent-held Calc supervisor is independent of the child
                # owner process and can observe its exact generation afterward.
                report = owner.close()
            except Exception as error:
                report={'status':'cleanup_failed','error':repr(error),
                    'release_attempted':True,'release_confirmed':False,
                    'cleanup_status':'UNKNOWN','verified':False,
                    'task_success':None,'replay_allowed':False}
            for prepared_id,entry in list(calc_launches.items()):
                supervisor=entry.get('supervisor')
                if supervisor is None:
                    continue
                try:
                    exit_receipt=supervisor.wait_for_verified_exit(timeout_s=5.0)
                except Exception as error:
                    exit_receipt={'status':'unknown','reason':'target_exit_observation_failed',
                        'error':repr(error),'task_success':None,'replay_allowed':False}
                if isinstance(exit_receipt,dict) and exit_receipt.get('verified') is True:
                    clean_exits[prepared_id]=deepcopy(exit_receipt)
                calc_lifecycle.append({'prepared_call_id':prepared_id,
                    'target_process_exit_receipt':deepcopy(exit_receipt)})
            for row in calc_lifecycle:
                prepared_id=row['prepared_call_id']
                entry=calc_launches[prepared_id]
                supervisor=entry.get('supervisor')
                if prepared_id not in clean_exits:
                    cleanup=None
                    cleanup_method=getattr(owner,'_cleanup_retained_calc_process_group',None)
                    if callable(cleanup_method):
                        try:
                            cleanup=cleanup_method()
                        except Exception as error:
                            cleanup={'status':'unknown','reason':'parent_cleanup_failed',
                                'error':repr(error),'verified_empty':False,
                                'clean_exit_verified':False,'task_success':None,
                                'replay_allowed':False}
                    if cleanup is None:
                        cleanup={'status':'unknown','reason':'parent_custody_unavailable',
                            'verified_empty':False,'clean_exit_verified':False,
                            'task_success':None,'replay_allowed':False}
                    row['process_group_cleanup']=deepcopy(cleanup)
                    entry['cleanup']=deepcopy(cleanup)
                    row['target_process_exit_receipt']={'status':'unknown',
                        'reason':'forced_cleanup_is_not_clean_exit',
                        'task_success':None,'replay_allowed':False}
                else:
                    row['process_group_cleanup']={'status':'not_needed',
                        'verified_empty':None,'clean_exit_verified':True,
                        'task_success':None,'replay_allowed':False}
                    entry['exit_receipt']=deepcopy(clean_exits[prepared_id])
                if supervisor is not None:
                    try:
                        supervisor.close()
                    except Exception as error:
                        row['log_close_error']=repr(error)
                with calls_lock:
                    prepared=calls.get(prepared_id,{})
                    compiled_id=prepared.get('artifact_consumed_by')
                    if compiled_id in calls and prepared_id in clean_exits:
                        calls[compiled_id]['target_process_exit_receipt']=deepcopy(
                            clean_exits[prepared_id])
            if calc_lifecycle:
                report['calc_target_lifecycle']=calc_lifecycle
            _write_json(root / ('session-' + owner.session_id + '-close.json'), report)
            return report
        finally:
            if cancellation_executor is not None:
                cancellation_executor.shutdown(wait=True, cancel_futures=False)

    @asynccontextmanager
    async def lifespan(_server):
        nonlocal shutting_down, server_shutdown_started
        try:
            yield {}
        finally:
            server_shutdown_started = True
            shutting_down = True
            # Finish committed workers before touching their connection. No
            # cancellation-based redispatch or close racing with active input.
            with anyio.CancelScope(shield=True):
                if workers and guarded_owned_process:
                    done, pending = await asyncio.wait(list(workers), timeout=5.0)
                    if pending:
                        owner.retire('server shutdown exceeded guarded worker drain bound')
                        await asyncio.wait(pending, timeout=2.0)
                elif workers:
                    # Teardown's waiter must not cancel the invocation's own
                    # completion obligation if that waiter is interrupted.
                    await asyncio.gather(*(asyncio.shield(worker) for worker in list(workers)),
                                         return_exceptions=True)
                if owner is not None:
                    await asyncio.to_thread(close_owner)

    server = PublicArgumentMCP('Agent Interface public API', lifespan=lifespan, instructions=(
        'Configured target names: ' + json.dumps(sorted(targets)) + '. ' +
        ('Each call owns one backend session. ' if owner is None else
         'One guarded X11 connection remains until close or transport shutdown; no reopen. '
         'Use session.binding_revision (initially 1) for dispatch. Explicit target review advances it. '
         if guarded else
         'One supervised Win32 target session remains until interface_close or transport shutdown; '
         'no automatic reopen. ' if supervised_win32 else
         'One X11 connection is retained until interface_close or transport shutdown; no automatic reopen. '
         'Use session.binding_revision (initially 1) for dispatch. Explicit target review advances it. ') +
        ('Guarded mode provides bridge source sequences and internally bounded guarded input; '
         'one explicit target, image-grounded aliases, no automatic replay. ' if guarded else
         'No source/lease is issued by this server. ') +
        'Inspect action, image and cleanup outcomes separately. '
        'Never replay an uncertain action automatically.'))

    def invoke(admission, operation, kwargs, compact, report_refs, detail="full", observation_refs=False,
               registered_call_id=None, wait_for_result_ms=None):
        nonlocal calc_preparation_slot, calc_preparation_deadline_ns
        if not admission.enter():
            return None  # A rejected/cancelled queued submission must never invoke.
        call_id = registered_call_id
        previous_interrupted_execution = getattr(
            getattr(getattr(owner, 'session', None), 'backend', None), 'interrupted_execution', None)
        try:
            call_root = root / (registered_call_id or uuid.uuid4().hex)
            call_root.mkdir(exist_ok=False)
            call_id = call_root.name
            with calls_lock:
                calls[call_id] = {"call_id": call_id, "operation": operation,
                                  "state": "running", "arguments": deepcopy(kwargs),
                                  "backend_attempted": False, "persistence_failure": None}
                if operation == 'guarded_calc_compiled':
                    calls[call_id].update(
                        profile_id=kwargs.get('profile_id'),
                        attempt_id=kwargs.get('attempt_id'))
                if wait_for_result_ms is not None:
                    calls[call_id]['response_wait_ms'] = wait_for_result_ms
            # Serialize before calling the backend. A persistence failure here sends no input.
            authored_program = deepcopy(kwargs.get('program'))
            request = {'operation': operation, 'arguments': kwargs,
                       'targets': deepcopy(getattr(owner, 'targets', targets)) if owner else targets,
                       'display_name': display_name}
            if wait_for_result_ms is not None: request['response_wait_ms'] = wait_for_result_ms
            if owner is not None:
                request['session'] = owner.snapshot()
            if detail != 'full':
                request['presentation'] = {'detail': detail}
            try:
                _write_json(call_root / 'request.json', request)
            except (OSError, ValueError, TypeError) as error:
                with calls_lock:
                    calls[call_id]['persistence_failure'] = 'request'
                return content({'status': 'invalid_request',
                    'error': 'REQUEST_PERSISTENCE_FAILED', 'detail': repr(error),
                    'failure_phase': 'request_persistence', 'operation_invoked': False,
                    'call_id': call_id, 'call_directory': str(call_root),
                    'replay_allowed': False}, error=True)
            if operation == 'guarded_calc_launch':
                prepared_call_id=kwargs.get('prepared_call_id')
                with calls_lock:
                    prepared=calls.get(prepared_call_id)
                    artifact=calc_artifacts.get(prepared_call_id)
                    expired=(calc_preparation_slot==prepared_call_id
                        and calc_preparation_deadline_ns is not None
                        and time.monotonic_ns()>=calc_preparation_deadline_ns)
                    if expired:
                        calc_artifacts.pop(prepared_call_id,None)
                        calc_preparation_slot=None
                        calc_preparation_deadline_ns=None
                        if prepared is not None:
                            prepared['reservation_expired']=True
                    launch_exists=bool(calc_launches)
                    valid=(_calc_launch_factory is not None
                        and calc_preparation_slot==prepared_call_id
                        and prepared is not None
                        and prepared.get('operation')=='guarded_calc_prepare'
                        and prepared.get('state')=='finished'
                        and artifact is not None
                        and not launch_exists)
                    if not valid:
                        calls[call_id].update(state='finished',backend_attempted=False,
                            predispatch_rejection='calc_launch_reservation_invalid_or_consumed')
                        return content({'status':'invalid_request',
                            'error':'CALC_LAUNCH_RESERVATION_INVALID_OR_CONSUMED',
                            'call_id':call_id,'operation_invoked':False,
                            'input_dispatched':False,'authority_granted':False,
                            'task_success':None,'replay_allowed':False},error=True)
                    prepared['calc_launch_attempted']=True
                    launch_entry={'prepared_call_id':prepared_call_id,
                        'attempt_id':prepared.get('attempt_id'),
                        'supervisor':None,'launch':None,'discovery':None,
                        'binding':None,'cleanup':None}
                    calc_launches[prepared_call_id]=launch_entry
                try:
                    owner.get()
                    supervisor=_calc_launch_factory(artifact)
                    required=('launch','discover_owned_window',
                        'review_and_bind_owned_window','wait_for_verified_exit',
                        'cleanup_owned_process_group','close')
                    if any(not callable(getattr(supervisor,name,None)) for name in required):
                        raise TypeError('configured Calc launch supervisor is incomplete')
                    launch_entry['supervisor']=supervisor
                    launched=supervisor.launch(artifact)
                    launch_entry['launch']=deepcopy(launched)
                    initial_custody=supervisor.retain_initial_process_group_custody(owner)
                    launch_entry['initial_custody']=deepcopy(initial_custody)
                    discovery=supervisor.discover_owned_window(owner,
                        title_hint=_calc_launch_title_hint,
                        deadline_s=_calc_discovery_deadline_s)
                    launch_entry['discovery']=deepcopy(discovery)
                    if discovery.get('status') != 'candidate_found':
                        launch_entry['cleanup']=deepcopy(
                            owner._cleanup_retained_calc_process_group())
                    report={'status':discovery.get('status','unknown'),
                        'prepared_call_id':prepared_call_id,
                        'attempt_id':launch_entry['attempt_id'],
                        'target_launch_status':launched.get('status'),
                        'parent_process_custody':('retained' if
                            getattr(owner,'_calc_process_group_custody',None)
                            is not None else 'not_established'),
                        'launch_receipt':deepcopy(launched),
                        'initial_process_group_custody':deepcopy(initial_custody),
                        'window_discovery':deepcopy(discovery),
                        'process_group_cleanup':deepcopy(launch_entry['cleanup']),
                        'authority_granted':False,'input_dispatched':False,
                        'task_success':None,'replay_allowed':False}
                    with calls_lock:
                        calls[prepared_call_id]['calc_launch_call_id']=call_id
                        calls[call_id].update(status=report['status'],
                            prepared_call_id=prepared_call_id,
                            target_launch_status=report['target_launch_status'],
                            parent_process_custody=report['parent_process_custody'])
                except Exception as error:
                    if (launch_entry['supervisor'] is not None
                            and launch_entry['supervisor'].launched
                            and getattr(owner,'_calc_process_group_custody',None) is not None):
                        try:
                            launch_entry['cleanup']=deepcopy(
                                owner._cleanup_retained_calc_process_group())
                        except Exception as cleanup_error:
                            launch_entry['cleanup']={'status':'unknown',
                                'reason':'parent_cleanup_failed','error':repr(cleanup_error),
                                'verified_empty':False,'clean_exit_verified':False,
                                'task_success':None,'replay_allowed':False}
                    report={'status':'unknown','error':'CALC_LAUNCH_OR_DISCOVERY_FAILED',
                        'detail':repr(error),'prepared_call_id':prepared_call_id,
                        'target_launch_status':('unknown' if launch_entry['supervisor'] is not None
                            and launch_entry['supervisor'].launched else 'not_attempted'),
                        'parent_process_custody':('retained' if
                            getattr(owner,'_calc_process_group_custody',None)
                            is not None else 'unknown'),
                        'process_group_cleanup':deepcopy(launch_entry['cleanup']),
                        'authority_granted':False,'input_dispatched':False,
                        'task_success':None,'replay_allowed':False}
                report.update(call_id=call_id,operation_invoked=True,
                    call_directory=str(call_root))
                try:
                    _write_json(call_root/'report.json',report)
                except (OSError,ValueError,TypeError) as error:
                    report['persistence_error']=repr(error)
                    report['replay_allowed']=False
                with calls_lock:
                    calls[call_id].update(report)
                return content(report,error=report.get('status') not in
                    ('candidate_found','unknown'))
            if operation == 'guarded_calc_prepare':
                with calls_lock:
                    if (calc_preparation_slot is not None
                            and calc_preparation_deadline_ns is not None
                            and time.monotonic_ns() >= calc_preparation_deadline_ns):
                        expired_id = calc_preparation_slot
                        calc_artifacts.pop(expired_id,None)
                        expired_record = calls.get(expired_id)
                        if expired_record is not None:
                            expired_record['reservation_expired'] = True
                        calc_preparation_slot = None
                        calc_preparation_deadline_ns = None
                    if calc_preparation_slot is not None:
                        calls[call_id].update(state='finished',
                            backend_attempted=False,
                            predispatch_rejection='calc_preparation_already_reserved')
                        return content({'status':'busy',
                            'error':'CALC_PREPARATION_ALREADY_RESERVED',
                            'call_id':call_id,'operation_invoked':False,
                            'input_dispatched':False,'task_success':None,
                            'replay_allowed':False},error=True)
                from runtime.guarded_x11_v1.calc_task_artifact_v1 import CalcTaskArtifact
                artifact = CalcTaskArtifact(call_root, call_id=call_id,
                    attempt_id=kwargs['attempt_id'],
                    expected_values=kwargs.get('task_values'),
                    task_plan=kwargs.get('task_plan'))
                with calls_lock:
                    calc_artifacts[call_id] = artifact
                    calc_preparation_deadline_ns = (
                        time.monotonic_ns() + _calc_preparation_ttl_ns)
                    calls[call_id].update(state='finished', prepared=True,
                        profile_id='calc-ocr-save-v1',
                        attempt_id=kwargs['attempt_id'],
                        reservation_expires_monotonic_ns=calc_preparation_deadline_ns)
                    calc_preparation_slot = call_id
                result = {'status':'prepared','call_id':call_id,
                    'attempt_id':kwargs['attempt_id'],
                    'task_values':dict(artifact.expected_values),
                    'task_plan_sha256':artifact.task_plan_sha256,
                    'expires_in_ms':_calc_preparation_ttl_ns // 1_000_000,
                    'artifact_path':str(artifact.path),
                    'artifact_name':'task-artifact.fods',
                    'target_launch_status':'not_attempted',
                    'parent_process_custody':'not_established',
                    'operation_invoked':False,'input_dispatched':False,
                    'task_success':None,'replay_allowed':False}
                _write_json(call_root / 'report.json', result)
                return content(result)
            task_artifact = None
            if operation == 'guarded_calc_compiled':
                prepared_call_id = kwargs.get('prepared_call_id')
                if _calc_launch_factory is not None:
                    launch_entry=calc_launches.get(prepared_call_id)
                    if (prepared_call_id is None or launch_entry is None
                            or not isinstance(launch_entry.get('binding'),dict)
                            or launch_entry['binding'].get('status')!='reviewed'):
                        calls[call_id].update(state='finished',
                            backend_attempted=False,
                            predispatch_rejection='launched_calc_window_review_and_bind_required')
                        return content({'status':'needs_review',
                            'error':'CALC_LAUNCH_REVIEW_BIND_REQUIRED',
                            'call_id':call_id,'operation_invoked':False,
                            'input_dispatched':False,'authority_granted':False,
                            'task_success':None,'replay_allowed':False},error=True)
                if prepared_call_id:
                    with calls_lock:
                        prepared = calls.get(prepared_call_id)
                        candidate = calc_artifacts.get(prepared_call_id)
                        expired = (calc_preparation_slot == prepared_call_id
                            and calc_preparation_deadline_ns is not None
                            and time.monotonic_ns() >= calc_preparation_deadline_ns)
                        if expired:
                            calc_artifacts.pop(prepared_call_id,None)
                            calc_preparation_slot = None
                            calc_preparation_deadline_ns = None
                            if prepared is not None:
                                prepared['reservation_expired'] = True
                        if (calc_preparation_slot != prepared_call_id
                                or prepared is None
                                or prepared.get('operation') != 'guarded_calc_prepare'
                                or prepared.get('state') != 'finished'
                                or prepared.get('attempt_id') != kwargs.get('attempt_id')
                                or candidate is None
                                or candidate.call_id != prepared_call_id
                                or candidate.attempt_id != kwargs.get('attempt_id')):
                            calls[call_id].update(state='finished',
                                backend_attempted=False,
                                predispatch_rejection='prepared_artifact_invalid_or_consumed')
                            return content({'status':'invalid_request',
                                'error':'CALC_PREPARED_ARTIFACT_INVALID_OR_CONSUMED',
                                'call_id':call_id,'operation_invoked':False,
                                'input_dispatched':False,'task_success':None,
                                'replay_allowed':False},error=True)
                        task_artifact = calc_artifacts.pop(prepared_call_id)
                        calc_preparation_slot = None
                        calc_preparation_deadline_ns = None
                        prepared['artifact_consumed_by'] = call_id
                        calls[call_id]['task_artifact_root_call_id'] = prepared_call_id
                        calls[call_id]['parent_task_plan'] = task_artifact.task_plan
                        calls[call_id]['parent_task_plan_sha256'] = (
                            task_artifact.task_plan_sha256)
            options = dict(kwargs, capture_directory=str(call_root / 'images'),
                           display_name=display_name)
            inspect_after = options.pop('inspect_after', None)
            inspect_after_region = options.pop('inspect_after_region', None)
            inspect_after_wait_ms = options.pop('inspect_after_wait_ms', None)
            # Attempt boundary only, not proof that the backend emitted input.
            with calls_lock:
                calls[call_id]['backend_attempted'] = True
            try:
                if operation == 'close':
                    report = close_owner()
                elif operation == 'recover_input':
                    report = owner.recover_input(**kwargs, capture_directory=str(call_root / 'images'))
                elif supervised_win32 and operation == 'recover_orphaned_input':
                    report = owner.recover_orphaned_input(**kwargs)
                elif operation == 'guarded_compiled':
                    report = owner.run_compiled_profile(
                        kwargs['interface'], kwargs['bindings'],
                        kwargs['predicate_rules'], kwargs['effect_rules'],
                        call_root, call_id)
                elif operation == 'guarded_review_window' and _calc_launch_factory is not None:
                    prepared_call_id=calc_preparation_slot
                    launch_entry=calc_launches.get(prepared_call_id)
                    candidate=(launch_entry.get('discovery',{}).get('candidate')
                        if isinstance(launch_entry,dict)
                        and isinstance(launch_entry.get('discovery'),dict) else None)
                    supervisor=(launch_entry.get('supervisor')
                        if isinstance(launch_entry,dict) else None)
                    if (supervisor is None or not isinstance(candidate,dict)
                            or candidate.get('xid')!=kwargs.get('window_id')):
                        report={'operation':operation,'status':'needs_review',
                            'error':'CALC_WINDOW_NOT_CURRENT_LAUNCH_CANDIDATE',
                            'input_dispatched':False,'authority_granted':False,
                            'task_success':None,'replay_allowed':False}
                    else:
                        report=supervisor.review_and_bind_owned_window(owner,
                            kwargs['window_id'],call_root=call_root/'calc-review')
                        if report.get('status')=='reviewed':
                            launch_entry['binding']=deepcopy(report)
                            launch_entry['bound_prepared_call_id']=prepared_call_id
                elif operation == 'guarded_calc_compiled':
                    report = owner.run_registered_calc_profile(
                        kwargs['profile_id'], kwargs['bindings'],
                        reviewed_sequence=kwargs['reviewed_sequence'],
                        reviewed_artifact_sha256=kwargs['reviewed_artifact_sha256'],
                        blank_reviewed=kwargs['blank_reviewed'],
                        attempt_id=kwargs['attempt_id'],
                        call_root=call_root, cancel_token=call_id,
                        task_artifact=task_artifact)
                elif operation.startswith('guarded_'):
                    report = owner.invoke_guarded(operation, kwargs, call_root)
                elif supervised_win32 and operation == 'dispatch':
                    try:
                        report = _run_supervised_win32_dispatch(owner,
                            supervised_win32_producer_factory, call_id, kwargs,
                            cancel_requested=lambda: _supervised_cancel_requested(call_id))
                    except (RuntimeError, ValueError) as error:
                        report = {'schema': 'agent-interface/runtime-dispatch-result-v1',
                            'status': 'invalid_request', 'error': str(error),
                            'operation_invoked': False, 'input_dispatched': False,
                            'release_confirmed': False, 'task_success': None,
                            'replay_allowed': False}
                elif supervised_win32 and operation == 'observe':
                    options.pop('display_name')
                    report = observe(deepcopy(targets), **options)
                elif operation in ('inspect_target', 'review_target'):
                    try:
                        review_options = dict(kwargs)
                        review_options['capture_directory'] = str(call_root / 'images')
                        report = getattr(owner, operation)(**review_options)
                    except Exception as error:
                        report = {'status': 'needs_review', 'error': repr(error),
                                  'input_dispatched': False, 'authority_granted': False}
                elif owner is not None:
                    options.pop('display_name')
                    if operation == 'observe':
                        if guarded_owned_process:
                            report = owner.observe(**options)
                        else:
                            report = observe_in_session(owner.get(), **options)
                    else:
                        program = options.pop('program')
                        report = owner.dispatch(program, **options)
                elif operation == 'observe':
                    report = observe(deepcopy(targets), **options)
                else:
                    program = options.pop('program')
                    report = dispatch(program, deepcopy(targets), **options)
            except Exception as error:
                # The call may already have emitted input. Never retry to recover a receipt.
                report = {'status': 'runtime_failed', 'error': repr(error),
                          'operation': operation, 'operation_invoked': True,
                          'effect_status': 'unknown'}
                if guarded_owned_process and owner is not None:
                    session_state = owner.snapshot()
                    report.update(release_confirmed=False, task_success=None,
                                  replay_allowed=False, cleanup_status='UNKNOWN',
                                  owner_process=session_state.get('owner_process'),
                                  late_server_request_possible=True)
                if owner is not None and owner.state == 'failed' and owner.session is None:
                    report.update(status='backend_unavailable', failure_phase='session_initialization',
                                  operation_invoked=False, input_dispatched=False, effect_status='none')
            if operation == 'dispatch' and inspect_after is not None:
                try:
                    capture_options = ({'screen_region': inspect_after_region,
                                        'capture_directory': str(call_root / 'images')}
                                       if inspect_after_region is not None else {})
                    if inspect_after_wait_ms is not None:
                        capture_options['wait_ms'] = inspect_after_wait_ms
                    report['post_dispatch_inspection'] = owner.inspect_after_dispatch(
                        report, inspect_after, **capture_options)
                except Exception as error:
                    report['post_dispatch_inspection'] = {
                        'status': 'needs_review', 'error': repr(error),
                        'input_dispatched': False, 'authority_granted': False,
                        'scope': 'Inspection failed after dispatch; original execution retained. No replay.'}
            if operation.startswith('guarded_'):
                report.setdefault('replay_allowed', False)
                report.setdefault('task_success', None)
            if operation == 'guarded_calc_compiled':
                # These exact child-returned values are copied into the parent
                # ledger before any client can tamper with report.json. They
                # describe admission and a save request, not a GUI save proof.
                with calls_lock:
                    calls[call_id]['task_artifact_admission'] = deepcopy(
                        report.get('task_artifact_admission'))
                    calls[call_id]['task_save_request'] = deepcopy(
                        report.get('task_save_request'))
                    calls[call_id]['task_method_receipt'] = deepcopy(
                        report.get('method_receipt'))
                    calls[call_id]['target_process_exit_receipt'] = deepcopy(
                        report.get('target_process_exit_receipt'))
                    calls[call_id]['task_artifact_root_call_id'] = report.get(
                        'task_artifact_root_call_id', calls[call_id].get(
                            'task_artifact_root_call_id', call_id))
            if operation == 'guarded_window_metadata':
                with calls_lock:
                    calls[call_id]['window_metadata'] = deepcopy(
                        report.get('window_metadata'))
            elif operation == 'guarded_window_metadata_revalidate':
                with calls_lock:
                    calls[call_id]['window_metadata_revalidation'] = deepcopy(report)
            if owner is not None:
                report['session'] = owner.snapshot()
            try:
                _write_json(call_root / 'report.json', report)
                persistence_error = None
            except OSError as error:
                persistence_error = repr(error)
                with calls_lock:
                    calls[call_id]['persistence_failure'] = 'report'
            # Orphan recovery is a control receipt, not an image observation.
            # Passing it through review_bytes requires a `records` batch and
            # masks a successful release as image_status=needs_review. Preserve
            # the exact recovery fields in the public response instead.
            result = (dict(report) if operation == 'recover_orphaned_input' else
                      present_management_report(report, call_root) if (operation.startswith('guarded_') or operation in ('close', 'inspect_target', 'review_target', 'recover_input')) else
                      present_result(report, call_root, compact=compact, report_refs=report_refs))
            if owner is not None:
                result['session'] = owner.snapshot()
            if 'post_dispatch_inspection' in report:
                result['post_dispatch_inspection'] = deepcopy(report['post_dispatch_inspection'])
            result['call_directory'] = str(call_root)
            result['call_id'] = call_id
            if persistence_error is not None:
                result['persistence_error'] = persistence_error
                result['replay_allowed'] = False
            if detail == 'brief':
                if operation.startswith('guarded_'):
                    from .guarded_presentation import brief_guarded_report
                    result = brief_guarded_report(result)
                elif operation == 'dispatch':
                    from .public_presentation import brief_public_report
                    result = brief_public_report(result)
            if detail == 'summary' and operation == 'dispatch':
                from .public_summary import summarize_public_dispatch
                result = summarize_public_dispatch(result, source_program=authored_program)
            if observation_refs and operation.startswith('guarded_'):
                from .receipt_references import compact_guarded_observation
                result = compact_guarded_observation(result)
            # Inspection's successful result is evidence awaiting caller review,
            # not a failed tool execution. This grants no target/input authority.
            inspection_ready = (
                operation == 'inspect_target' and report.get('status') == 'needs_review'
                and report.get('error') is None
                and isinstance(report.get('review_request'), dict)
                and report['review_request'].get('tool') == 'interface_review_target'
                and (kwargs.get('screen_region') is None or result.get('image_status') == 'image'))
            return content(result, error=persistence_error is not None or (
                (operation.startswith('guarded_') or operation in (
                    'close', 'inspect_target', 'review_target', 'recover_input',
                    'recover_orphaned_input')) and
                (report.get('error') is not None or report.get('status') in ('cleanup_failed','refused','recovery_failed')
                 or (operation == 'recover_orphaned_input'
                     and report.get('status') == 'unknown')
                 or (report.get('status') == 'needs_review' and not inspection_ready)
                 or report.get('feedback_status') == 'observation_failed')))
        except BaseException as error:
            if not isinstance(error, Exception) and call_id is not None:
                with calls_lock:
                    record = calls.get(call_id)
                    if record is not None:
                        record['worker_interrupted'] = type(error).__name__
                        record['interruption_receipt'] = False
                if record is not None:
                    try:
                        interruption = dict(status='runtime_interrupted', error=repr(error),
                            exception_type=type(error).__name__, operation=operation,
                            operation_invoked=record['backend_attempted'], effect_status='unknown',
                            release_confirmed=False, task_success=None, replay_allowed=False,
                            authority_granted=False,
                            report_artifact_present=(call_root / 'report.json').is_file())
                        if owner is not None:
                            interruption['session'] = owner.snapshot()
                            execution = getattr(getattr(owner.session, 'backend', None),
                                                'interrupted_execution', None)
                            # A prior recovered call's snapshot is not evidence
                            # for this interruption, including presentation faults.
                            if isinstance(execution, dict) and execution is not previous_interrupted_execution:
                                interruption['interrupted_execution'] = deepcopy(execution)
                        # Keep any completed backend report byte-for-byte. A
                        # separate receipt records the interrupted call boundary.
                        _write_json(call_root / 'interruption.json', interruption)
                        with calls_lock:
                            record['interruption_receipt'] = True
                    except BaseException as persistence_error:
                        # Receipt failures cannot replace the worker's original
                        # stop or trigger input/recovery/reconnect.
                        with calls_lock:
                            record['interruption_persistence_failure'] = repr(persistence_error)
            raise
        finally:
            if call_id is not None:
                with calls_lock:
                    calls[call_id]["state"] = "finished"
                    supervised_cancel_requests.discard(call_id)
            admission.finish()

    async def submit(operation, kwargs, compact, report_refs, detail="full", observation_refs=False, *, wait_for_result_ms=None):
        nonlocal shutting_down
        if wait_for_result_ms is not None and (operation not in ('guarded_input','guarded_recover_input','guarded_compiled','guarded_calc_compiled','guarded_calc_prepare','guarded_calc_launch','recover_orphaned_input')
                and not (supervised_win32 and operation == 'dispatch')
                or type(wait_for_result_ms) is not int or not 0<=wait_for_result_ms<=10000):
            return content({'status':'invalid_request','error':'INVALID_RESPONSE_WAIT',
                            'operation_invoked':False,'replay_allowed':False},error=True)
        if report_refs and not compact:
            return content({'status': 'invalid_request',
                'error': 'report_refs requires compact=true',
                'operation_invoked': False}, error=True)
        if ((shutting_down and operation != 'close')
                or (owner is not None and owner.state == 'closed' and operation != 'close')):
            return content({'status': 'session_closed', 'operation_invoked': False,
                            'replay_allowed': False}, error=True)
        if (operation == 'guarded_calc_compiled' and guarded_owned_process
                and owner is not None):
            # Model planning can outlive the reviewed source. Reject a source
            # already known stale before scheduling the owner operation; the
            # child profile still revalidates to cover changes after this check.
            snapshot = owner.snapshot()
            current_sequence = snapshot.get('observation_sequence')
            if (type(current_sequence) is not int
                    or kwargs.get('reviewed_sequence') != current_sequence):
                return content({
                    'status':'invalid_request',
                    'error':'CALC_REVIEW_SOURCE_STALE',
                    'detail':'reviewed source is no longer the current owner observation',
                    'current_sequence':current_sequence,
                    'operation_invoked':False,
                    'input_dispatched':False,
                    'release_confirmed':None,
                    'effect_status':'unknown',
                    'task_success':None,
                    'replay_allowed':False},error=True)
        # Decide busy before scheduling a worker; thread-pool contention must not queue input.
        if not lock.acquire(blocking=False):
            return content({'status': 'busy', 'operation_invoked': False}, error=True)
        # Register invocation custody before asking the executor. It can raise
        # after callable entry or return a failed handle while input still runs.
        loop = asyncio.get_running_loop()
        completion = loop.create_future()
        workers.add(completion)
        completion.add_done_callback(workers.discard)
        def completed():
            loop.call_soon_threadsafe(completion.set_result, None)
        admission = _WorkerAdmission(lock, completed)
        registered_call_id = None
        def finish_unentered_record(error):
            if registered_call_id is not None:
                with calls_lock:
                    calls[registered_call_id].update(state='finished',worker_error=repr(error))
        try:
            # Submit synchronously so pre-worker rejection is handled here. Keep
            # to_thread's context propagation and shield accepted work below.
            context = contextvars.copy_context()
            if wait_for_result_ms is not None:
                candidate = uuid.uuid4().hex
                with calls_lock:
                    if candidate in calls: raise RuntimeError('call ID collision')
                    calls[candidate] = dict(call_id=candidate,operation=operation,state='queued',
                        arguments=deepcopy(kwargs),backend_attempted=False,persistence_failure=None,
                        response_wait_ms=wait_for_result_ms)
                    registered_call_id = candidate
            worker = loop.run_in_executor(
                None, context.run, invoke, admission, operation, kwargs,
                compact, report_refs, detail, observation_refs,registered_call_id,wait_for_result_ms)
        except BaseException as error:
            revoked = admission.revoke_pending()
            if revoked:
                finish_unentered_record(error)
                rollback_unentered_close(operation, revoked)
            if not isinstance(error, Exception):
                # Preserve cancellation/fatal exception propagation after
                # revoking only work that has not entered the callable.
                raise
            report = {'status': 'worker_submission_failed',
                'failure_phase': 'worker_submission', 'error': repr(error),
                'operation_invoked': not revoked,
                'input_dispatched': False if revoked else None,
                'effect_status': 'none' if revoked else 'unknown',
                'replay_allowed': False}
            if registered_call_id is not None: report['call_id'] = registered_call_id
            return content(report, error=True)
        def finished(task):
            # A terminal future can fail/cancel before callable entry. Revoke
            # only pending work; a running worker still owns its slot.
            revoked = admission.revoke_pending()
            if revoked:
                finish_unentered_record('executor handle terminated before invocation')
                rollback_unentered_close(operation, revoked)
            if not task.cancelled():
                task.exception()
        worker.add_done_callback(finished)
        # A cancelled transport must not cancel a queued worker and strand its lock.
        try:
            if wait_for_result_ms is not None:
                # asyncio.wait never cancels accepted work when its timer ends.
                await asyncio.wait({worker},timeout=wait_for_result_ms/1000)
                if not worker.done():
                    with calls_lock: record = deepcopy(calls[registered_call_id])
                    return content(dict(status='pending',call_id=registered_call_id,call=record,
                        scope='current_server',result_available=False,release_confirmed=False,
                        effect_status='unknown',task_success=None,replay_allowed=False,
                        note='Response wait ended; original worker retains custody and may still execute. '
                             'Retrieve this call ID. Pending does not cancel input or permit replay.'))
            return await asyncio.shield(worker)
        except BaseException as error:
            # A terminal executor handle can surface its error before its done
            # callback runs. Revoke unentered work before returning to a caller
            # that may immediately submit again. A live/queued worker retains
            # custody when only this transport await was cancelled.
            if worker.done():
                revoked = admission.revoke_pending()
                if revoked:
                    finish_unentered_record('executor handle terminated before invocation')
                    rollback_unentered_close(operation, revoked)
            handle_cancelled = (isinstance(error,asyncio.CancelledError) and worker.cancelled()
                                and asyncio.current_task().cancelling()==0)
            if wait_for_result_ms is not None and (isinstance(error,Exception) or handle_cancelled):
                with calls_lock: record = deepcopy(calls[registered_call_id])
                return content(dict(status='worker_handle_failed',call_id=registered_call_id,call=record,
                    error=repr(error),operation_invoked=None,input_dispatched=None,effect_status='unknown',
                    result_available=False,release_confirmed=False,task_success=None,replay_allowed=False,
                    note='Executor handle failed; invocation custody is recorded separately. '
                         'Inspect this call ID. Never replay or assume cleanup from this error.'),error=True)
            raise

    if owner is not None and not guarded and not guarded_win32:
        @server.tool()
        async def interface_recover_input(current_binding_revision: StrictInt,
                                          target: StrictStr | None = None,
                                          region: list[StrictInt] | None = None) -> CallToolResult:
            """Explicitly release tracked inputs after unverified cleanup, without replay.

            Requires this open persistent-X11 session, its current binding revision,
            and recovery_required=true. Failed readback leaves recovery blocked.
            Verified empty release clears only the input block and advances binding
            revision, invalidating old programs and pending target reviews. No new
            lease is issued. Optional target and region=[x,y,width,height] together
            capture that window after successful recovery in this call. Capture
            failure retains the recovery result and new revision; observe separately.
            Review the image before choosing a new program. Capture is not a redraw
            acknowledgement or task-success check. Never retries automatically.
            """
            return await submit('recover_input', {'current_binding_revision': current_binding_revision,
                                                 'target': target, 'region': region}, False, False)

        @server.tool()
        async def interface_inspect_target(target: StrictStr,
                                           screen_region: list[StrictInt] | None = None) -> CallToolResult:
            """Read the focused managed client in this target's configured transient family.

            Does not select, focus or send input. Returns a one-use 30s review ID
            and review_request with exact tool arguments for explicit caller review.
            Successful inspection returns isError=false while status remains needs_review.
            This candidate request is not executed and retained results do not renew it.
            Optional screen_region=[x,y,width,height] returns a fresh screen image
            in this call. Metadata is rechecked after capture; disagreement gives
            no review ID. This is not an atomic snapshot or redraw acknowledgement.
            WM metadata is not authenticated identity.
            """
            return await submit('inspect_target', {'target': target, 'screen_region': screen_region}, False, False)

        @server.tool()
        async def interface_review_target(target: StrictStr, window_id: StrictInt,
                                          review_id: StrictStr,
                                          screen_region: list[StrictInt] | None = None) -> CallToolResult:
            """Explicitly select the inspected client after rechecking its evidence.

            Sends no input, never clears recovery, consumes the review ID and
            advances the session binding revision. Optional screen_region returns
            a fresh image after selection, with a metadata recheck. Selection stays
            committed even if capture fails or metadata changes. Review image and
            capture_consistency before input; otherwise capture the surface separately.
            Use the returned revision in new source assertions. No redraw acknowledgement.
            """
            return await submit('review_target', {'target': target, 'window_id': window_id,
                                                 'review_id': review_id,
                                                 'screen_region': screen_region}, False, False)

    if owner is not None:
        @server.tool()
        async def interface_close() -> CallToolResult:
            """Close this owned connection, retaining cleanup evidence; never reopen.

            Busy refuses while an operation runs. Retained results remain readable.
            This operation does not issue a new input release; inspect the retained
            action or cancellation receipt for its release evidence. Close results
            are separate from prior task outcomes.
            """
            nonlocal shutting_down
            # Reserve shutdown under the same lock used to admit cancellation.
            # close_owner shuts down the cancellation executor, so it must not
            # join an operation whose custody is still active.
            with calls_lock:
                if ((shutting_down and owner.state != 'closed')
                        or active_cancellation_operation is not None
                        or lock.locked()):
                    return content({'status':'busy', 'operation_invoked':False,
                        'release_confirmed':False, 'cleanup_status':'UNKNOWN',
                        'task_success':None, 'replay_allowed':False,
                        'cancellation_operation_id':active_cancellation_operation}, error=True)
                shutting_down = True
            return await submit('close', {}, False, False)

    @server.tool()
    async def interface_clock() -> CallToolResult:
        """Read this execution host's monotonic clock without input or authority.

        Use only on this live server connection when authoring an already
        authorized absolute expiry; this call issues no lease or source sequence.
        Transport/presentation time consumes the remaining deadline. Do not add
        elapsed Windows time, renew a retained sample, or reuse it after server
        replacement/suspend. No backend is opened and no action result is created.
        """
        return content({'schema': 'agent-interface/execution-clock-v1',
                        'monotonic_ns': time.monotonic_ns(),
                        'clock': 'time.monotonic_ns',
                        'clock_info': vars(time.get_clock_info('monotonic')),
                        'server_instance_id': server_instance_id,
                        'input_dispatched': False, 'authority_granted': False,
                        'lease_issued': False,
                        'scope': 'Clock sample only; not freshness, admission or task completion. '
                                 'Only comparable within this execution host clock domain.'})

    @server.tool()
    async def interface_validate(program: dict) -> CallToolResult:
        """Check a draft program's static syntax/expansion without input or a backend.

        Optional; not a prerequisite for dispatch. Does not check live capability,
        freshness, lease expiry or task success, and grants no runtime admission.
        No action call ID or retained result is created. Invalid programs return
        static_valid=false; correct the draft explicitly rather than retrying input.
        A nesting-limit input error returns static_valid=null, not a validity verdict.
        """
        try:
            row = inspect_program(program)
        except RecursionError:
            row = {'schema': VALIDATION_SCHEMA, 'status': 'input_error',
                   'static_valid': None, 'error': 'INPUT_NESTING_LIMIT',
                   'side_effect_authority': False, 'runtime_admission': 'not_evaluated',
                   'backend_checked': False, 'task_success': None}
        return content(row, error=row['static_valid'] is not True)

    if guarded:
        from .mcp_guarded import register_guarded_tools
        if guarded_owned_process:
            @server.tool()
            async def interface_guarded_window_metadata_revalidate(
                    metadata_call_id: Annotated[StrictStr,
                        Field(pattern=r'^[0-9a-f]{32}$')]) -> CallToolResult:
                """Re-query a recent explicit-XID metadata result from server memory.

                The source must be a finished metadata call that remains no older
                than 500 ms through the fresh isolated query, mapped and focused
                before/after. The query must match its cues and process/window
                incarnation. This grants no target selection or input authority.
                """
                with calls_lock:
                    source = deepcopy(calls.get(metadata_call_id))
                if (not isinstance(source, dict)
                        or source.get('operation') != 'guarded_window_metadata'
                        or source.get('state') != 'finished'
                        or not isinstance(source.get('window_metadata'), dict)):
                    return content({'status':'unknown_call',
                        'metadata_call_id':metadata_call_id,'same_window':False,
                        'operation_invoked':False,'input_dispatched':False,
                        'authority_granted':False,'task_success':None,
                        'replay_allowed':False}, error=True)
                source_metadata = source['window_metadata']
                observed_ns = source_metadata.get('observed_monotonic_ns')
                now_ns = time.monotonic_ns()
                if (type(observed_ns) is not int or observed_ns > now_ns
                        or now_ns - observed_ns > 500_000_000):
                    return content({'status':'stale_or_unfocused',
                        'metadata_call_id':metadata_call_id,'same_window':False,
                        'reason':'source_expired_or_not_focused',
                        'operation_invoked':False,'input_dispatched':False,
                        'authority_granted':False,'task_success':None,
                        'replay_allowed':False})
                return await submit('guarded_window_metadata_revalidate',
                    {'source_metadata':source_metadata,
                     'metadata_call_id':metadata_call_id},False,False)

            @server.tool()
            async def interface_verify_task(
                    call_id: Annotated[StrictStr, Field(pattern=r'^[0-9a-f]{32}$')]
                    ) -> CallToolResult:
                """Verify only a terminal registered Calc call after verified close.

                This read-only verifier accepts no path, values, or caller receipt.
                It also requires a parent-held exit receipt for the exact Calc
                target generation; retirement of the X11 input owner alone is
                insufficient. Missing target-exit or Save custody remains
                unknown; parsed content alone does not establish that the
                managed GUI produced the artifact.
                """
                with calls_lock:
                    record = deepcopy(calls.get(call_id))
                if (record is None or record.get('operation') != 'guarded_calc_compiled'
                        or record.get('profile_id') != 'calc-ocr-save-v1'):
                    return content({'status':'unknown_call','call_id':call_id,
                        'task_success':None,'operation_invoked':False,
                        'input_dispatched':False,'replay_allowed':False,
                        'scope':'guarded_x11_calc'}, error=True)
                if record.get('state') != 'finished':
                    return content({'status':'pending','call_id':call_id,
                        'task_success':None,'operation_invoked':False,
                        'input_dispatched':False,'replay_allowed':False,
                        'scope':'guarded_x11_calc'})
                # A close operation is serialized after the Calc call by the
                # public API. The child receipt is retained in owner.close_report;
                # the call-directory report is presentation, not authority.
                close_receipt = deepcopy(getattr(owner, 'close_report', None))
                if (not isinstance(close_receipt, dict)
                        or close_receipt.get('status') != 'closed'
                        or close_receipt.get('verified') is not True
                        or close_receipt.get('owner_process_retired') is not True
                        or close_receipt.get('release_confirmed') is not True):
                    return content({'status':'unknown','call_id':call_id,
                        'task_success':None,'reason':'verified_close_required',
                        'operation_invoked':False,'input_dispatched':False,
                        'replay_allowed':False,'scope':'guarded_x11_calc'}, error=True)
                attempt_id = record.get('attempt_id')
                descriptor = record.get('task_artifact_admission')
                save_request = record.get('task_save_request')
                artifact_root_call_id = record.get('task_artifact_root_call_id',call_id)
                if (not isinstance(descriptor, dict)
                        or descriptor.get('profile_id') != 'calc-ocr-save-v1'
                        or descriptor.get('attempt_id') != attempt_id):
                    effect = {'status':'unknown','task_success':None,
                              'reason':'artifact_admission_unavailable'}
                else:
                    from runtime.guarded_x11_v1.calc_task_artifact_v1 import (
                        make_registered_calc_save_controller_receipt,
                        verify_task_artifact_descriptor)
                    save_controller = make_registered_calc_save_controller_receipt(
                        descriptor=descriptor,
                        method_receipt=record.get('task_method_receipt'),
                        save_request=save_request,
                        parent_task_plan=record.get('parent_task_plan'),
                        parent_task_plan_sha256=record.get(
                            'parent_task_plan_sha256'))
                    effect = verify_task_artifact_descriptor(root / artifact_root_call_id,
                        descriptor=descriptor,save_request=save_request,
                        close_receipt=close_receipt,
                        target_exit_receipt=record.get('target_process_exit_receipt'),
                        trusted_save_controller_receipt=save_controller)
                return content({'status':effect.get('status','unknown'),
                    'call_id':call_id,'attempt_id':attempt_id,
                    'task_effect':effect,'task_success':effect.get('task_success'),
                    'operation_invoked':False,'input_dispatched':False,
                    'replay_allowed':False,'scope':'guarded_x11_calc'},
                    error=effect.get('status') != 'verified')

        def complete_cancellation(call_id, operation_id):
            nonlocal active_cancellation_operation, unarchived_cancellation_call_id
            try:
                with calls_lock:
                    record = calls.get(call_id)
                    cancellation = (record.get('cancellation')
                        if isinstance(record, dict) else None)
                    transaction_deadline_ns = (cancellation.get(
                        'transaction_deadline_monotonic_ns')
                        if isinstance(cancellation, dict) else None)
                result = owner.cancel_guarded(call_id,
                    operation_id=operation_id,
                    deadline_monotonic_ns=transaction_deadline_ns)
                if not isinstance(result, dict):
                    raise TypeError('cancellation result must be a mapping')
                result = deepcopy(result)
                result.setdefault('release_confirmed', False)
                result.setdefault('cleanup_status', 'UNKNOWN')
                result.setdefault('task_success', None)
                result.setdefault('replay_allowed', False)
                terminal = {'status':'completed', 'result':deepcopy(result),
                            'completed_monotonic_ns':time.monotonic_ns()}
            except BaseException as error:
                result = {'status':'cancel_unconfirmed', 'error':repr(error),
                          'release_confirmed':False, 'cleanup_status':'UNKNOWN',
                          'task_success':None, 'replay_allowed':False}
                terminal = {'status':'unknown', 'result':deepcopy(result),
                            'error':repr(error),
                            'completed_monotonic_ns':time.monotonic_ns()}
            with calls_lock:
                record = calls.get(call_id)
                cancellation = record.get('cancellation') if record else None
                persisted = deepcopy(cancellation) if isinstance(cancellation, dict) else {}
            persisted.update(deepcopy(terminal))
            # Persist only after the cleanup call has returned. A slow/failing
            # evidence write cannot delay release; pending remains conservative.
            archive_succeeded = False
            try:
                _write_json(root / call_id / 'cancellation.json',
                            persisted)
                archive_succeeded = True
            except (OSError, ValueError, TypeError) as error:
                terminal['persistence_failure'] = repr(error)
            with calls_lock:
                record = calls.get(call_id)
                if record is not None:
                    cancellation = record.get('cancellation')
                    if isinstance(cancellation, dict) and cancellation.get('operation_id') == operation_id:
                        cancellation.update(terminal)
                        if archive_succeeded:
                            record['cancellation_operation_id'] = operation_id
                            record['cancellation_archived'] = True
                            record.pop('cancellation', None)
                        else:
                            unarchived_cancellation_call_id = call_id
                cancellation_futures.pop(operation_id, None)
                if active_cancellation_operation == operation_id:
                    active_cancellation_operation = None
            return result

        async def cancel_guarded(call_id):
            nonlocal active_cancellation_operation, unarchived_cancellation_call_id
            # No worker slot, filesystem or input emission on this path. The
            # one-worker executor keeps owned-process cancellation off the MCP
            # event loop while one operation retains custody after response timeout.
            operation_id = None
            future = None
            direct_cancel = False
            archived_lookup = False
            with calls_lock:
                record = calls.get(call_id)
                valid_call = (record is not None
                    and record['operation'] in ('guarded_input','guarded_compiled',
                                                  'guarded_calc_compiled')
                    and (record['state'] == 'running' or 'cancellation' in record
                         or (cancellation_executor is not None
                             and record.get('cancellation_archived') is True)))
                if valid_call and cancellation_executor is None:
                    direct_cancel = True
                elif valid_call:
                    cancellation = record.get('cancellation')
                    if cancellation is None and record.get('cancellation_archived') is True:
                        archived_lookup = True
                    elif isinstance(cancellation, dict):
                        operation_id = cancellation['operation_id']
                        future = cancellation_futures.get(operation_id)
                        if future is None:
                            return content(dict(cancellation.get('result') or {
                                'status':'pending' if cancellation.get('status') == 'pending' else 'cancel_unconfirmed',
                                'release_confirmed':False, 'cleanup_status':'UNKNOWN',
                                'task_success':None, 'replay_allowed':False},
                                operation_id=operation_id, cancellation=deepcopy(cancellation),
                                call_id=call_id))
                    else:
                        if record['state'] != 'running':
                            valid_call = False
                        elif shutting_down:
                            return content({'status':'session_closed', 'call_id':call_id,
                                'operation_invoked':False, 'release_confirmed':False,
                                'cleanup_status':'UNKNOWN', 'task_success':None,
                                'replay_allowed':False})
                        elif active_cancellation_operation is not None:
                            return content({'status':'cancel_busy', 'call_id':call_id,
                                'operation_invoked':False, 'release_confirmed':False,
                                'cleanup_status':'UNKNOWN', 'task_success':None,
                                'replay_allowed':False})
                        elif unarchived_cancellation_call_id is not None:
                            return content({'status':'cancel_capacity_exhausted',
                                'operation_invoked':False, 'release_confirmed':False,
                                'cleanup_status':'UNKNOWN', 'task_success':None,
                                'replay_allowed':False,
                                'note':'A prior terminal cancellation receipt could not be archived; '
                                       'the in-memory custody slot is retained.'})
                        else:
                            observed = owner.snapshot()
                            process = observed.get('owner_process') or {}
                            operation_id = uuid.uuid4().hex
                            admitted_ns = time.monotonic_ns()
                            cancellation = {
                                'operation_id':operation_id,
                                'status':'pending',
                                'admitted_monotonic_ns':admitted_ns,
                                'caller_response_deadline_monotonic_ns':(
                                    admitted_ns + _GUARDED_CANCEL_CALLER_RESPONSE_BUDGET_NS),
                                'transaction_deadline_monotonic_ns':admitted_ns + int(
                                    _guarded_cancel_transaction_timeout_s * 1_000_000_000),
                                'owner_generation':{
                                    'session_id':observed.get('session_id'),
                                    'child_pid':process.get('pid'),
                                    'x_resource_base':process.get('x_client_resource_base'),
                                    'binding_revision':observed.get('binding_revision')},
                                'release_confirmed':False, 'task_success':None,
                                'replay_allowed':False}
                            record['cancellation'] = cancellation
                            active_cancellation_operation = operation_id
                            try:
                                future = cancellation_executor.submit(
                                    complete_cancellation, call_id, operation_id)
                            except RuntimeError as error:
                                cancellation.update(status='unknown', error=repr(error),
                                    result={'status':'cancel_unconfirmed', 'error':repr(error),
                                        'release_confirmed':False, 'cleanup_status':'UNKNOWN',
                                        'task_success':None, 'replay_allowed':False},
                                    completed_monotonic_ns=time.monotonic_ns())
                                active_cancellation_operation = None
                                unarchived_cancellation_call_id = call_id
                                return content(dict(cancellation['result'], call_id=call_id,
                                    operation_id=operation_id, cancellation=deepcopy(cancellation)))
                            cancellation_futures[operation_id] = future
            if not valid_call:
                return content({'status':'not_active','input_dispatched':False,'release_confirmed':False})
            if archived_lookup:
                with calls_lock:
                    archived_call = deepcopy(calls.get(call_id))
                cancellation = (await load_cancellation_record(call_id, archived_call)
                    if archived_call is not None else None)
                if cancellation is None:
                    return content({'status':'cancel_unconfirmed', 'call_id':call_id,
                        'release_confirmed':False, 'cleanup_status':'UNKNOWN',
                        'task_success':None, 'replay_allowed':False})
                return content(dict(cancellation.get('result') or {
                    'status':'cancel_unconfirmed', 'release_confirmed':False,
                    'cleanup_status':'UNKNOWN', 'task_success':None,
                    'replay_allowed':False}, call_id=call_id,
                    operation_id=cancellation.get('operation_id'),
                    cancellation=cancellation))
            if direct_cancel:
                return content(owner.cancel_guarded(call_id))
            wrapped = asyncio.wrap_future(future)
            # Resume the public caller before its deadline so event-loop scheduling,
            # receipt lookup, and response encoding fit inside the advertised budget.
            remaining_ns = (cancellation['caller_response_deadline_monotonic_ns']
                            - time.monotonic_ns())
            remaining = max(0, remaining_ns
                            - _GUARDED_CANCEL_RESPONSE_HANDOFF_MARGIN_NS) / 1_000_000_000
            done, _ = await asyncio.wait({wrapped}, timeout=remaining)
            with calls_lock:
                call_record = deepcopy(calls.get(call_id))
            current = (await load_cancellation_record(call_id, call_record)
                if call_record is not None else None)
            if not done:
                return content({'status':'pending', 'call_id':call_id,
                    'operation_id':operation_id, 'cancellation':current,
                    'result_available':True, 'release_confirmed':False,
                    'cleanup_status':'UNKNOWN', 'task_success':None,
                    'replay_allowed':False,
                    'note':'The response wait ended; this cancellation operation retains custody. '
                           'Retrieve it through interface_results. Pending permits no replay.'})
            result = deepcopy(current.get('result') or {
                'status':'cancel_unconfirmed', 'release_confirmed':False,
                'cleanup_status':'UNKNOWN', 'task_success':None,
                'replay_allowed':False})
            return content(dict(result, call_id=call_id, operation_id=operation_id,
                                cancellation=current))
        register_guarded_tools(server, submit,
            cancel=cancel_guarded if guarded_query_worker else None,
            compiled_enabled=guarded_owned_process,
            window_lifecycle_enabled=guarded_window_lifecycle,
            calc_launch_enabled=_calc_launch_factory is not None)
    elif guarded_win32:
        from .mcp_win32 import register_guarded_win32_tools
        register_guarded_win32_tools(server, owner, content,
            producer_factory=_guarded_win32_producer_factory,
            task_oracle=_guarded_win32_task_oracle)
    else:
        @server.tool()
        async def interface_observe(target: StrictStr, frame: Literal['window_client', 'screen_physical_px'],
                              region: list[StrictInt], compact: StrictBool = False, report_refs: StrictBool = False) -> CallToolResult:
            """Capture once without input; return receipt and native image block.

            Region is [x, y, width, height]; public dispatch observe ops accept
            the same region array (do not mix with legacy x/y/w/h fields).
            On X11, window_client coordinates are
            relative to the target client; overlapping dialogs may be absent or black.
            screen_physical_px coordinates are relative to the display and include
            other visible windows in that region. Choose an explicit screen region
            when an overlapping dialog is needed to interpret the target's state.
            A capture is not a redraw or task-completion acknowledgement.
            On Win32, the full receipt exposes a stable target_generation at
            receipt.source.raw_report.target_generation; include it in
            source.target_generations for matching focused dispatches.
            report_refs requires compact=true and a v3 receipt decoder.
            In v3, read the full report at receipt.source.raw_report in this response;
            the report reference requires no additional tool call.
            """
            return await submit('observe', {'target': target, 'frame': frame, 'region': region}, compact, report_refs)

        @server.tool()
        async def interface_dispatch(program: PublicProgram, current_observation_seq: StrictInt,
                               current_binding_revision: StrictInt,
                               compact: StrictBool = False, report_refs: StrictBool = False,
                               detail: Literal["full", "brief", "summary"] = "full",
                               inspect_after: StrictStr | None = None,
                               inspect_after_region: list[StrictInt] | None = None,
                               inspect_after_wait_ms: StrictInt | None = None,
                               wait_for_result_ms: StrictInt | None = None) -> CallToolResult:
            """Dispatch once through core admission. Include observe for an image; no implicit replay.

            Observation sequence is a caller assertion, not server-issued freshness.
            Persistent mode requires session.binding_revision (initially 1); review
            advances it. One-shot binding values remain caller assertions.
            A returned image may precede redraw. Release and cleanup failures remain visible.
            inspect_after names a configured target in persistent-x11 mode. After
            completed, released input, return read-only target review metadata;
            no implicit selection. With inspect_after_region, capture that explicit
            screen_physical_px region once after verified release and recheck target
            metadata. Optional inspect_after_wait_ms (0..1000) explicitly sleeps after
            verified release before capture; capture_wait records that sleep, not a
            redraw acknowledgement. Default adds no wait. This grants no input
            authority and does not extend the input lease. The selected image names
            post_dispatch_observation_id. Without
            a region inspection is metadata only, later than the inline image.
            Inspection failure preserves input evidence. Summary preserves complete
            successful inspection context; errors or skipped inspection stay full.
            detail=brief with compact/report_refs summarizes supported successful paced
            dispatches. This is a partial receipt; presentation.retrieve gets full data.
            detail=summary also supports nonpaced completed dispatches and omits
            duplicated provenance; follow presentation.retrieve for full evidence.
            Both partial modes require compact=true, report_refs=true.
            Failures and unsupported results stay full. Images are unchanged.
            report_refs requires compact=true. Full v3 receipts keep the full report
            at receipt.source.raw_report; brief receipts use report_projection and
            require explicit retrieval for omitted detail.
            """
            if inspect_after is not None and (session_mode != 'persistent-x11' or inspect_after not in owner.targets):
                return content({'status': 'invalid_request', 'error': 'INVALID_POST_DISPATCH_INSPECTION',
                                'operation_invoked': False, 'input_dispatched': False}, error=True)
            if inspect_after_region is not None:
                from .observe import valid_observation_request
                if (inspect_after is None or not valid_observation_request(
                        inspect_after, 'screen_physical_px', inspect_after_region)):
                    return content({'status': 'invalid_request',
                        'error': 'INVALID_POST_DISPATCH_CAPTURE',
                        'operation_invoked': False, 'input_dispatched': False}, error=True)
            if inspect_after_wait_ms is not None and (inspect_after_region is None
                    or not 0 <= inspect_after_wait_ms <= 1000):
                return content({'status': 'invalid_request', 'error': 'INVALID_POST_DISPATCH_CAPTURE_WAIT',
                                'operation_invoked': False, 'input_dispatched': False}, error=True)
            if wait_for_result_ms is not None and not supervised_win32:
                return content({'status': 'invalid_request',
                    'error': 'RESPONSE_WAIT_REQUIRES_SUPERVISED_WIN32',
                    'operation_invoked': False, 'input_dispatched': False}, error=True)
            arguments = {'program': program, 'current_observation_seq': current_observation_seq,
                         'current_binding_revision': current_binding_revision}
            if inspect_after is not None:
                arguments['inspect_after'] = inspect_after
            if inspect_after_region is not None:
                arguments['inspect_after_region'] = inspect_after_region
            if inspect_after_wait_ms is not None:
                arguments['inspect_after_wait_ms'] = inspect_after_wait_ms
            return await submit('dispatch', arguments, compact, report_refs, detail,
                                wait_for_result_ms=wait_for_result_ms)

    if supervised_win32:
        if callable(task_oracle):
            @server.tool()
            async def interface_verify_task(
                    call_id: Annotated[StrictStr, Field(pattern=r'^[0-9a-f]{32}$')],
                    wait_for_result_ms: Annotated[StrictInt, Field(ge=0, le=10000)] = 2000
                    ) -> CallToolResult:
                """Verify one terminal action with the server-configured independent task oracle.

                The caller supplies only the exact action call ID. The oracle,
                its evidence source and its identity are configured inside the
                server; clients cannot submit a self-asserted success receipt.
                """
                existing = owner.interface_result(call_id)
                if existing is None:
                    return content({'status':'unknown_call','call_id':call_id,
                        'operation_invoked':False,'task_success':None,
                        'replay_allowed':False,'scope':'supervised_win32'}, error=True)
                action = existing.get('action') or {}
                if action.get('status') not in ('completed','recovered'):
                    status = ('pending' if action.get('status') in
                              ('pending','queued','running','cancel_pending') else 'unknown')
                    return content({'status':status,'call_id':call_id,
                        'action_status':action.get('status'),'task_success':None,
                        'operation_invoked':False,'input_dispatched':False,
                        'replay_allowed':False,'scope':'supervised_win32'})
                try:
                    reserved = owner.begin_task_effect_verification(call_id)
                except ValueError:
                    return content({'status':'unknown_call','call_id':call_id,
                        'operation_invoked':False,'task_success':None,
                        'replay_allowed':False,'scope':'supervised_win32'}, error=True)
                if not reserved:
                    existing = owner.interface_result(call_id)
                    effect = (existing or {}).get('task_effect')
                    if not isinstance(effect, dict):
                        effect = {'status':'unknown','task_success':None}
                    return content({'status':effect.get('status','unknown'),
                        'call_id':call_id,'task_effect':effect,
                        'task_success':effect.get('task_success'),
                        'operation_invoked':False,'input_dispatched':False,
                        'replay_allowed':False,'scope':'supervised_win32'},
                        error=effect.get('status')=='unknown')
                task = asyncio.create_task(asyncio.to_thread(
                    task_oracle, {'call_id':call_id, **action}))
                task_oracle_tasks.add(task)

                def task_oracle_finished(done):
                    task_oracle_tasks.discard(done)
                    if not done.cancelled():
                        done.exception()

                task.add_done_callback(task_oracle_finished)
                done, _ = await asyncio.wait({task},
                    timeout=max(0, wait_for_result_ms * 1_000_000
                                - _GUARDED_CANCEL_RESPONSE_HANDOFF_MARGIN_NS)
                    / 1_000_000_000)
                if not done:
                    row = owner.fail_task_effect_verification(
                        call_id, 'independent_task_oracle_response_timeout')
                else:
                    try:
                        row = owner.record_task_effect(call_id, task.result())
                    except Exception as error:
                        row = owner.fail_task_effect_verification(call_id,
                            'independent_task_oracle_receipt_invalid: ' + repr(error))
                effect = row['task_effect']
                return content({'status':effect['status'],'call_id':call_id,
                    'task_effect':effect,'task_success':effect['task_success'],
                    'operation_invoked':False,'input_dispatched':False,
                    'replay_allowed':False,'scope':'supervised_win32'},
                    error=effect['status']=='unknown')

        @server.tool()
        async def interface_cancel(call_id: Annotated[StrictStr, Field(pattern=r'^[0-9a-f]{32}$')]) -> CallToolResult:
            """Cancel the exact supervised standard dispatch and retain custody."""
            with calls_lock:
                call = calls.get(call_id)
                if call is None:
                    return content({'status': 'unknown_call', 'call_id': call_id,
                        'operation_invoked': False, 'replay_allowed': False}, error=True)
                if call.get('state') == 'finished':
                    return content({'status': 'not_cancellable', 'call_id': call_id,
                        'operation_invoked': False, 'replay_allowed': False})
                supervised_cancel_requests.add(call_id)
            existing = owner.interface_result(call_id)
            if existing is None:
                return content({'status': 'cancel_pending', 'call_id': call_id,
                    'release_confirmed': False, 'task_success': None,
                    'input_dispatched': False, 'replay_allowed': False,
                    'scope': 'supervised_win32',
                    'note': 'Cancellation is retained before operation admission; '
                            'the dispatch worker will close admission before producer start.'})
            result = owner.cancel_guarded(call_id,
                cleanup_deadline_ns=time.monotonic_ns() + _SUPERVISED_WIN32_CLEANUP_NS)
            result.update(operation_invoked=False, input_dispatched=False,
                task_success=None, replay_allowed=False, scope='supervised_win32')
            return content(result)

        @server.tool()
        async def interface_recover_orphaned_input(
                source_operation_id: Annotated[StrictStr, Field(pattern=r'^[0-9a-f]{32}$')],
                source_target_generation: Annotated[StrictStr, Field(pattern=r'^[0-9a-f]{64}$')],
                recovery_target_generation: Annotated[StrictStr, Field(pattern=r'^[0-9a-f]{64}$')],
                obligations: list[StrictStr],
                source_custody_record: dict[str, object]
                ) -> CallToolResult:
            """Attempt one bounded native release for an audited prior-server custody record.

            Requires a fresh supervised-Win32 session with no admitted action,
            the exact source target generation, a separately observed current
            recovery target generation for the configured logical target,
            frozen obligations, and the
            retained UNKNOWN custody record with the source producer observed
            absent, including the boolean `late_server_request_possible` from
            the terminal source receipt. If that flag is true, release/readback
            alone is insufficient: the supervisor must also complete its
            configured independent late-input horizon or the session remains
            fenced against new actions. The server checks those fields and
            hashes the canonical record into its receipt; this is a trace digest,
            not an authenticity signature. A successful recovery proves release
            and neutral readback, plus the bounded horizon when the source receipt
            says late requests remain possible. The source action remains UNKNOWN,
            replay stays denied, and any next action requires a fresh generation.
            """
            return await submit('recover_orphaned_input', {
                'source_operation_id': source_operation_id,
                'source_target_generation': source_target_generation,
                'recovery_target_generation': recovery_target_generation,
                'obligations': obligations,
                'source_custody_record': source_custody_record},
                False, False, wait_for_result_ms=6000)

    @server.tool()
    async def interface_results(call_id: StrictStr | None = None,
                                before_call_id: StrictStr | None = None,
                                compact: StrictBool = False,
                                include_image: StrictBool = True,
                                report_refs: StrictBool = False,
                                detail: Literal["full", "brief", "summary"] = "full",
                                observation_refs: StrictBool = False) -> CallToolResult:
        """List this server's calls or reread one retained result. Never dispatch or observe.

        A finished worker is not proof of task success. Unknown calls are not replayed.
        This registry lasts only for this server process; no restart recovery is implied.
        Set include_image=false to inspect metadata without resending a retained image.
        detail=brief projects normal guarded checks or supported successful paced
        public dispatches with compact/report_refs. detail=summary summarizes
        known successful public dispatches, including nonpaced programs.
        Full is the default; failures
        and unsupported reports stay full. Retrieval never replays input.
        observation_refs=true replaces an exact duplicate observation with a local
        reference to source.native; expand_guarded_observation restores the view.
        It changes no image, capture, authority, or retained raw report.
        report_refs requires compact=true and a v3 receipt decoder.
        In v3, read the full report at receipt.source.raw_report in this response;
        the report reference requires no additional tool call.
        """
        if report_refs and not compact:
            return content({'status': 'invalid_request',
                'error': 'report_refs requires compact=true',
                'operation_invoked': False}, error=True)
        if guarded_win32 or supervised_win32:
            if call_id is None:
                rows = owner.list_results()
                return content({'status': 'call_list', 'scope': 'current_server',
                    'total_calls': len(rows), 'calls': rows[:20],
                    'operation_invoked': False,
                    'note': 'Win32 action receipt lookup requires its exact call_id.'})
            if before_call_id is not None:
                return content({'status': 'invalid_request',
                    'error': 'call_id and before_call_id are mutually exclusive',
                    'operation_invoked': False}, error=True)
            row = owner.interface_result(call_id)
            if row is None:
                # A response-waiting dispatch is registered in the MCP call
                # ledger before its worker admits the operation to the native
                # owner. During that interval the exact call is valid but the
                # owner has no action receipt yet. Preserve the pending state
                # instead of misclassifying it as an unknown call.
                with calls_lock:
                    pending_record = deepcopy(calls.get(call_id))
                if pending_record is not None and pending_record.get('state') != 'finished':
                    if pending_record.get('cancellation_archived') is True:
                        pending_record['cancellation'] = await load_cancellation_record(
                            call_id, pending_record)
                    pending_record.pop('cancellation_archived', None)
                    pending_record.pop('cancellation_operation_id', None)
                    return content({'status': 'pending', 'call': pending_record,
                        'cancellation': deepcopy(pending_record.get('cancellation')),
                        'operation_invoked': False})
                # A finished MCP call can still have a durable report even if
                # the owner has no action row (for example, pre-admission
                # rejection). Let the ordinary exact-call receipt path below
                # resolve it before declaring the ID unknown.
            else:
                # Lease expiry may return the dispatch worker while native
                # recovery is still pending. In that schedule the worker's
                # one-shot progress read has ended before the producer is
                # retired. A later exact-call readback can safely capture the
                # retained lower bound after recovery becomes terminal. This
                # diagnostic never upgrades release or task success.
                action = row.get('action')
                progress_reader = getattr(
                    supervised_win32_producer_factory,
                    'read_program_actions_lower_bound', None)
                if (type(action) is dict
                        and action.get('status') in ('recovered', 'unknown')
                        and 'program_actions_capture_status' not in action
                        and 'program_actions_lower_bound' not in action):
                    if callable(progress_reader):
                        try:
                            owner.capture_program_emission_progress(call_id,
                                progress_reader)
                        except Exception as error:
                            try:
                                owner.record_program_emission_progress_failure(
                                    call_id, error)
                            except Exception:
                                pass
                    else:
                        try:
                            owner.record_program_emission_progress_failure(
                                call_id,
                                RuntimeError('progress_reader_unavailable'))
                        except Exception:
                            pass
                    row = owner.interface_result(call_id)
                row = deepcopy(row)
                row['operation_invoked'] = False
                row['input_dispatched'] = False
                effect = row.get('task_effect')
                row['task_success'] = (effect.get('task_success')
                    if isinstance(effect, dict) and effect.get('status') == 'verified'
                    else None)
                row['replay_allowed'] = False
                return content(row)
        with calls_lock:
            if call_id is None:
                # Most recent calls first, bounded; request details are available by ID.
                if before_call_id is not None and before_call_id not in calls:
                    return content({'status': 'unknown_cursor', 'operation_invoked': False}, error=True)
                ids = iter(reversed(calls))
                if before_call_id is not None:
                    ids = dropwhile(lambda item: item != before_call_id, ids)
                    next(ids, None)  # Continue strictly before the previously returned ID.
                page = list(islice(ids, 21))
                rows = [calls[item] for item in page[:20]]
                return content({'status': 'call_list', 'scope': 'current_server',
                    'total_calls': len(calls), 'calls': [
                        {key: row[key] for key in ('call_id', 'operation', 'state')}
                        for row in rows],
                    'next_before_call_id': page[19] if len(page) > 20 else None,
                    'operation_invoked': False})
            if before_call_id is not None:
                return content({'status': 'invalid_request',
                    'error': 'call_id and before_call_id are mutually exclusive',
                    'operation_invoked': False}, error=True)
            record = deepcopy(calls.get(call_id))
        if record is None:
            return content({'status': 'unknown_call', 'operation_invoked': False}, error=True)
        if record.get('cancellation_archived') is True:
            record['cancellation'] = await load_cancellation_record(call_id, record)
        public_record = deepcopy(record)
        public_record.pop('cancellation_archived', None)
        public_record.pop('cancellation_operation_id', None)
        if record['state'] != 'finished':
            return content({'status': 'pending', 'call': public_record,
                'cancellation':deepcopy(record.get('cancellation')),
                'operation_invoked': False})
        if record.get('worker_interrupted') and not record.get('interruption_receipt'):
            return content({'status': 'receipt_unavailable', 'call': record,
                'error': 'INTERRUPTION_RECEIPT_UNAVAILABLE', 'operation_invoked': False,
                'replay_allowed': False}, error=True)
        call_root = root / call_id  # Only IDs minted and held by this server are accepted.
        try:
            receipt = call_root / ('interruption.json' if record.get('interruption_receipt') else 'report.json')
            report = json.loads(await asyncio.to_thread(receipt.read_text,
                                                       encoding='utf-8'))
        except (OSError, ValueError) as error:
            return content({'status': 'receipt_unavailable', 'call': record,
                'error': repr(error), 'operation_invoked': False,
                'replay_allowed': False}, error=True)
        result = (await asyncio.to_thread(present_management_report, report, call_root, include_image=include_image) if (record['operation'].startswith('guarded_') or record['operation'] in ('close', 'inspect_target', 'review_target', 'recover_input')) else
                  await asyncio.to_thread(present_result, report, call_root, compact=compact, report_refs=report_refs, include_image=include_image))
        if 'post_dispatch_inspection' in report:
            result['post_dispatch_inspection'] = deepcopy(report['post_dispatch_inspection'])
        result.update(call_id=call_id, call_directory=str(call_root), retained_call=public_record,
                      operation_invoked=False)
        if record.get('cancellation') is not None:
            result['cancellation'] = deepcopy(record['cancellation'])
        if detail == 'brief' and record['operation'].startswith('guarded_'):
            from .guarded_presentation import brief_guarded_report
            result = brief_guarded_report(result)
        if detail == 'brief' and record['operation'] == 'dispatch':
            from .public_presentation import brief_public_report
            result = brief_public_report(result)
        if detail == 'summary' and record['operation'] == 'dispatch':
            from .public_summary import summarize_public_dispatch
            result = summarize_public_dispatch(result, source_program=record["arguments"].get("program"))
        if observation_refs and record['operation'].startswith('guarded_'):
            from .receipt_references import compact_guarded_observation
            result = compact_guarded_observation(result)
        return content(result, include_image=include_image)

    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--targets', type=Path, required=True)
    parser.add_argument('--output-directory', type=Path, required=True)
    parser.add_argument('--display')
    parser.add_argument('--session-mode', choices=('one-shot', 'persistent-x11', 'guarded-x11',
                                                   'supervised-win32'), default='one-shot')
    parser.add_argument('--supervised-win32-late-input-horizon-ms', type=int,
                        default=0, metavar='MS',
                        help='sample neutral Win32 input after normal completion or confirmed cancellation release for 1..60000 ms; zero disables horizon sampling')
    parser.add_argument('--guarded-process-identity', action='store_true',
                        help='require sampled Linux/XRes process identity in guarded-x11 mode; trusted local PID namespace required')
    parser.add_argument('--guarded-query-worker',action='store_true',
                        help='isolate active focus/process queries; requires guarded-x11 and process identity, qualified same local X server')
    parser.add_argument('--guarded-observation-worker',action='store_true',
                        help='isolate active visual checks; requires guarded query worker and qualified same local X server')
    parser.add_argument('--guarded-window-lifecycle',action='store_true',
                        help='require direct target lifecycle evidence; requires guarded query worker')
    parser.add_argument('--guarded-retention-mode', choices=('files', 'journal'), default='files',
                        help='guarded-x11 receipt storage; journal is opt-in and fsyncs each record')
    parser.add_argument('--guarded-owned-process',action='store_true',
                        help='run the complete guarded-X11 session in one spawned owner process; requires process identity and query worker')
    parser.add_argument('--guarded-prestarted-cancel-supervisor',action='store_true',
                        help='prestart a one-shot cancellation supervisor; requires --guarded-owned-process')
    parser.add_argument('--calc-launcher-executable', type=Path,
                        help='fixed absolute Debian LibreOffice oosplash executable; enables parent-custodied Calc launch')
    parser.add_argument('--calc-gui-executable', type=Path,
                        help='fixed absolute Debian LibreOffice soffice.bin executable')
    parser.add_argument('--calc-window-title-hint', default='task-artifact.fods')
    parser.add_argument('--calc-discovery-deadline-s', type=float, default=20.0)
    args = parser.parse_args()
    if (args.supervised_win32_late_input_horizon_ms < 0
            or args.supervised_win32_late_input_horizon_ms > 60_000):
        parser.error('--supervised-win32-late-input-horizon-ms must be between 0 and 60000')
    if (args.supervised_win32_late_input_horizon_ms
            and args.session_mode != 'supervised-win32'):
        parser.error('--supervised-win32-late-input-horizon-ms requires --session-mode supervised-win32')
    if args.guarded_process_identity and args.session_mode != 'guarded-x11':
        parser.error('--guarded-process-identity requires --session-mode guarded-x11')
    if args.guarded_query_worker and (args.session_mode != 'guarded-x11' or not args.guarded_process_identity):
        parser.error('--guarded-query-worker requires guarded-x11 and --guarded-process-identity')
    if args.guarded_observation_worker and not args.guarded_query_worker:
        parser.error('--guarded-observation-worker requires --guarded-query-worker')
    if args.guarded_window_lifecycle and not args.guarded_query_worker:
        parser.error('--guarded-window-lifecycle requires --guarded-query-worker')
    if args.guarded_owned_process and (args.session_mode != 'guarded-x11'
            or not args.guarded_process_identity or not args.guarded_query_worker):
        parser.error('--guarded-owned-process requires guarded-x11, --guarded-process-identity and --guarded-query-worker')
    if args.guarded_retention_mode == 'journal' and args.session_mode != 'guarded-x11':
        parser.error('--guarded-retention-mode journal requires --session-mode guarded-x11')
    if args.guarded_prestarted_cancel_supervisor and not args.guarded_owned_process:
        parser.error('--guarded-prestarted-cancel-supervisor requires --guarded-owned-process')
    calc_paths=(args.calc_launcher_executable,args.calc_gui_executable)
    if any(value is not None for value in calc_paths):
        if any(value is None for value in calc_paths):
            parser.error('--calc-launcher-executable and --calc-gui-executable must be configured together')
        if (args.session_mode!='guarded-x11' or not args.guarded_process_identity
                or not args.guarded_query_worker or not args.guarded_window_lifecycle
                or not args.guarded_owned_process):
            parser.error('Calc launch requires guarded-x11, process identity, query worker, window lifecycle and owned-process mode')
        if any(not value.is_absolute() for value in calc_paths):
            parser.error('Calc executable paths must be absolute')
        if (not args.calc_window_title_hint or len(args.calc_window_title_hint)>128
                or not args.calc_window_title_hint.isprintable()
                or not math.isfinite(args.calc_discovery_deadline_s)
                or not 0 < args.calc_discovery_deadline_s <= 60):
            parser.error('Calc window discovery hint or deadline is invalid')
    options = {'guarded_process_identity':args.guarded_process_identity}
    if args.supervised_win32_late_input_horizon_ms:
        options['supervised_win32_late_input_horizon_ns'] = (
            args.supervised_win32_late_input_horizon_ms * 1_000_000)
    if args.guarded_query_worker: options['guarded_query_worker'] = True
    if args.guarded_observation_worker: options['guarded_observation_worker'] = True
    if args.guarded_window_lifecycle: options['guarded_window_lifecycle'] = True
    if args.guarded_retention_mode != 'files':
        options['guarded_retention_mode'] = args.guarded_retention_mode
    if args.guarded_owned_process: options['guarded_owned_process'] = True
    if args.guarded_prestarted_cancel_supervisor:
        options['guarded_prestarted_cancel_supervisor'] = True
    if args.calc_launcher_executable is not None:
        from runtime.guarded_x11_v1.calc_launcher_v1 import CalcLaunchSupervisor
        options['_calc_launch_factory'] = lambda artifact: CalcLaunchSupervisor(
            args.calc_launcher_executable,
            custody_mode='libreoffice-oosplash-child',
            oosplash_executable=args.calc_launcher_executable,
            gui_executable=args.calc_gui_executable)
        options['_calc_launch_title_hint'] = args.calc_window_title_hint
        options['_calc_discovery_deadline_s'] = args.calc_discovery_deadline_s
    create_server(json.loads(args.targets.read_text(encoding='utf-8')),
                  args.output_directory, display_name=args.display, session_mode=args.session_mode,
                  **options).run(transport='stdio')


if __name__ == '__main__':
    main()
