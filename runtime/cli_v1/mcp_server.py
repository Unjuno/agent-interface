"""Optional stdio MCP transport; one-shot by default, explicit persistent X11 option."""
import argparse
import asyncio
from concurrent.futures import ThreadPoolExecutor
import contextvars
from copy import deepcopy
from contextlib import asynccontextmanager
import json
from itertools import islice, dropwhile
from pathlib import Path
import threading
import time
from typing import Annotated, Literal
import uuid

from mcp.server.fastmcp import FastMCP
import anyio
from mcp.types import CallToolResult, ImageContent, TextContent
from pydantic import Field, StrictBool, StrictInt, StrictStr

from .api import dispatch
from .mcp_session import MCPSessionOwner
from .attempt import _write_json
from .observe import observe, observe_in_session
from .review import present_result
from .validate_program import SCHEMA as VALIDATION_SCHEMA, inspect_program


# Documentation metadata only: the public compiler and core remain the validators.
# Keep dict forwarding intact, including extensions and malformed-request receipts.
PublicProgram = Annotated[dict, Field(description=(
    'Bounded agent-interface/program-v1 object. Required fields: '
    'schema="agent-interface/program-v1", program_id (1..64 letters/digits/._-), '
    'source={observation_seq: integer, binding_revision: integer}, '
    'authority={lease_id: identifier, expires_at_ns: integer in the execution host monotonic clock}, '
    'terminal={release_all_required: true}, and ops (ordered objects). '
    'The caller must supply a valid current lease and matching source/binding assertions; '
    'this server does not mint them. Begin with {"op":"focus","target":"configured-name"} '
    'when input requires focus. On X11, each program containing pointer_move or observe '
    'must put focus or activate before those operations; a previous dispatch or '
    'interface_observe does not supply that program-local target. Focus does not '
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
    """Reject unknown top-level tool arguments before SDK coercion or input.

    Nested program/tail dictionaries retain their existing runtime validators.
    Only public FastMCP list/call methods are used; SDK metadata is not patched.
    """
    async def list_tools(self):
        tools = await super().list_tools()
        return [tool.model_copy(update={
            'inputSchema': {**tool.inputSchema, 'additionalProperties': False}
        }) for tool in tools]

    async def call_tool(self, name, arguments):
        for tool in await self.list_tools():
            if tool.name == name:
                unknown = sorted(set(arguments) - set(tool.inputSchema.get('properties', {})))
                if unknown:
                    return content({'status': 'invalid_request',
                        'error': 'unknown top-level tool arguments',
                        'unknown_arguments': unknown, 'operation_invoked': False,
                        'input_dispatched': False, 'replay_allowed': False}, error=True)
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
                  _guarded_owner_factory=None):
    if session_mode not in ("one-shot", "persistent-x11", "guarded-x11"):
        raise ValueError("unknown session mode")
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
    if (not isinstance(targets, dict) or not targets or
            any(not isinstance(k, str) or not k or type(v) is not int or v <= 0
                for k, v in targets.items())):
        raise ValueError('explicit nonempty target name -> positive native ID mapping required')
    if type(guarded_owned_process) is not bool:
        raise ValueError('guarded_owned_process must be a boolean')
    if guarded_owned_process and (session_mode != 'guarded-x11'
            or not guarded_process_identity or not guarded_query_worker):
        raise ValueError('guarded owned process requires guarded-x11, process identity and query worker')
    targets = deepcopy(targets)
    root = Path(output_directory).resolve()
    root.mkdir(parents=True, exist_ok=True)
    lock = threading.Lock()
    workers = set()
    calls = {}
    calls_lock = threading.Lock()
    cancellation_executor = (ThreadPoolExecutor(max_workers=1,
        thread_name_prefix='guarded-cancel') if guarded_owned_process else None)
    cancellation_futures = {}
    active_cancellation_operation = None
    if cancellation_executor is not None:
        # Pay thread startup before the first safety-sensitive cancellation.
        cancellation_executor.submit(lambda: None).result(timeout=5)
    owner = MCPSessionOwner(targets, display_name) if session_mode == 'persistent-x11' else None
    guarded = session_mode == 'guarded-x11'
    if guarded:
        from .mcp_guarded import GuardedSessionOwner
        owner_options = dict(process_identity=guarded_process_identity,
                             query_worker=guarded_query_worker,
                             observation_worker=guarded_observation_worker,
                             window_lifecycle=guarded_window_lifecycle)
        if guarded_owned_process:
            from .owned_guarded_session import OwnedGuardedSessionOwner
            owner = OwnedGuardedSessionOwner(targets, root, display_name,
                **owner_options, _owner_factory=_guarded_owner_factory)
        else:
            owner = GuardedSessionOwner(targets, root, display_name, **owner_options)
    shutting_down = False
    server_instance_id = uuid.uuid4().hex

    def close_owner():
        try:
            report = owner.close()
            _write_json(root / ('session-' + owner.session_id + '-close.json'), report)
            return report
        finally:
            if cancellation_executor is not None:
                cancellation_executor.shutdown(wait=True, cancel_futures=False)

    @asynccontextmanager
    async def lifespan(_server):
        nonlocal shutting_down
        try:
            yield {}
        finally:
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
         'One guarded X11 connection remains until close or transport shutdown; no reopen. ' if guarded else
         'One X11 connection is retained until interface_close or transport shutdown; no automatic reopen. '
         'Use session.binding_revision (initially 1) for dispatch. Explicit target review advances it. ') +
        ('Guarded mode provides bridge source sequences and internally bounded guarded input; '
         'one explicit target, image-grounded aliases, no automatic replay. ' if guarded else
         'No source/lease is issued by this server. ') +
        'Inspect action, image and cleanup outcomes separately. '
        'Never replay an uncertain action automatically.'))

    def invoke(admission, operation, kwargs, compact, report_refs, detail="full", observation_refs=False,
               registered_call_id=None, wait_for_result_ms=None):
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
                if wait_for_result_ms is not None:
                    calls[call_id]['response_wait_ms'] = wait_for_result_ms
            # Serialize before calling the backend. A persistence failure here sends no input.
            authored_program = deepcopy(kwargs.get('program'))
            request = {'operation': operation, 'arguments': kwargs, 'targets': deepcopy(owner.targets) if owner else targets,
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
                elif operation == 'guarded_compiled':
                    report = owner.run_compiled_profile(
                        kwargs['interface'], kwargs['bindings'],
                        kwargs['predicate_rules'], kwargs['effect_rules'],
                        call_root, call_id)
                elif operation.startswith('guarded_'):
                    report = owner.invoke_guarded(operation, kwargs, call_root)
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
            if owner is not None:
                report['session'] = owner.snapshot()
            try:
                _write_json(call_root / 'report.json', report)
                persistence_error = None
            except OSError as error:
                persistence_error = repr(error)
                with calls_lock:
                    calls[call_id]['persistence_failure'] = 'report'
            result = (present_management_report(report, call_root) if (operation.startswith('guarded_') or operation in ('close', 'inspect_target', 'review_target', 'recover_input')) else
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
                (operation.startswith('guarded_') or operation in ('close', 'inspect_target', 'review_target', 'recover_input')) and
                (report.get('error') is not None or report.get('status') in ('cleanup_failed','refused','recovery_failed')
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
            admission.finish()

    async def submit(operation, kwargs, compact, report_refs, detail="full", observation_refs=False, *, wait_for_result_ms=None):
        if wait_for_result_ms is not None and (operation not in ('guarded_input','guarded_recover_input','guarded_compiled')
                or type(wait_for_result_ms) is not int or not 0<=wait_for_result_ms<=10000):
            return content({'status':'invalid_request','error':'INVALID_RESPONSE_WAIT',
                            'operation_invoked':False,'replay_allowed':False},error=True)
        if report_refs and not compact:
            return content({'status': 'invalid_request',
                'error': 'report_refs requires compact=true',
                'operation_invoked': False}, error=True)
        if shutting_down or (owner is not None and owner.state == 'closed' and operation != 'close'):
            return content({'status': 'session_closed', 'operation_invoked': False,
                            'replay_allowed': False}, error=True)
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
            if revoked: finish_unentered_record(error)
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
            if revoked: finish_unentered_record('executor handle terminated before invocation')
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
                if revoked: finish_unentered_record('executor handle terminated before invocation')
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

    if owner is not None and not guarded:
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
            Release/close failures are separate from prior task outcomes.
            """
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
        def complete_cancellation(call_id, operation_id):
            nonlocal active_cancellation_operation
            try:
                result = owner.cancel_guarded(call_id)
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
            try:
                _write_json(root / call_id / 'cancellation.json',
                            persisted)
            except (OSError, ValueError, TypeError) as error:
                terminal['persistence_failure'] = repr(error)
            with calls_lock:
                record = calls.get(call_id)
                if record is not None:
                    cancellation = record.get('cancellation')
                    if isinstance(cancellation, dict) and cancellation.get('operation_id') == operation_id:
                        cancellation.update(terminal)
                cancellation_futures.pop(operation_id, None)
                if active_cancellation_operation == operation_id:
                    active_cancellation_operation = None
            return result

        async def cancel_guarded(call_id):
            nonlocal active_cancellation_operation
            # No worker slot, filesystem or input emission on this path. The
            # one-worker executor keeps owned-process cancellation off the MCP
            # event loop while one operation retains custody after response timeout.
            operation_id = None
            future = None
            direct_cancel = False
            with calls_lock:
                record = calls.get(call_id)
                valid_call = (record is not None
                    and record['operation'] in ('guarded_input','guarded_compiled')
                    and (record['state'] == 'running' or 'cancellation' in record))
                if valid_call and cancellation_executor is None:
                    direct_cancel = True
                elif valid_call:
                    cancellation = record.get('cancellation')
                    if isinstance(cancellation, dict):
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
                        elif active_cancellation_operation is not None:
                            return content({'status':'cancel_busy', 'call_id':call_id,
                                'operation_invoked':False, 'release_confirmed':False,
                                'cleanup_status':'UNKNOWN', 'task_success':None,
                                'replay_allowed':False})
                        else:
                            observed = owner.snapshot()
                            process = observed.get('owner_process') or {}
                            operation_id = uuid.uuid4().hex
                            admitted_ns = time.monotonic_ns()
                            cancellation = {
                                'operation_id':operation_id,
                                'status':'pending',
                                'admitted_monotonic_ns':admitted_ns,
                                'caller_response_deadline_monotonic_ns':admitted_ns + 300_000_000,
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
                                return content(dict(cancellation['result'], call_id=call_id,
                                    operation_id=operation_id, cancellation=deepcopy(cancellation)))
                            cancellation_futures[operation_id] = future
            if not valid_call:
                return content({'status':'not_active','input_dispatched':False,'release_confirmed':False})
            if direct_cancel:
                return content(owner.cancel_guarded(call_id))
            wrapped = asyncio.wrap_future(future)
            remaining = max(0, cancellation['caller_response_deadline_monotonic_ns'] - time.monotonic_ns()) / 1_000_000_000
            done, _ = await asyncio.wait({wrapped}, timeout=remaining)
            with calls_lock:
                current = deepcopy(calls[call_id].get('cancellation'))
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
            compiled_enabled=guarded_owned_process)
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
                               inspect_after_wait_ms: StrictInt | None = None) -> CallToolResult:
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
            arguments = {'program': program, 'current_observation_seq': current_observation_seq,
                         'current_binding_revision': current_binding_revision}
            if inspect_after is not None:
                arguments['inspect_after'] = inspect_after
            if inspect_after_region is not None:
                arguments['inspect_after_region'] = inspect_after_region
            if inspect_after_wait_ms is not None:
                arguments['inspect_after_wait_ms'] = inspect_after_wait_ms
            return await submit('dispatch', arguments, compact, report_refs, detail)

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
        if record['state'] != 'finished':
            return content({'status': 'pending', 'call': record,
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
        result.update(call_id=call_id, call_directory=str(call_root), retained_call=record,
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
    parser.add_argument('--session-mode', choices=('one-shot', 'persistent-x11', 'guarded-x11'), default='one-shot')
    parser.add_argument('--guarded-process-identity', action='store_true',
                        help='require sampled Linux/XRes process identity in guarded-x11 mode; trusted local PID namespace required')
    parser.add_argument('--guarded-query-worker',action='store_true',
                        help='isolate active focus/process queries; requires guarded-x11 and process identity, qualified same local X server')
    parser.add_argument('--guarded-observation-worker',action='store_true',
                        help='isolate active visual checks; requires guarded query worker and qualified same local X server')
    parser.add_argument('--guarded-window-lifecycle',action='store_true',
                        help='require direct target lifecycle evidence; requires guarded query worker')
    parser.add_argument('--guarded-owned-process',action='store_true',
                        help='run the complete guarded-X11 session in one spawned owner process; requires process identity and query worker')
    args = parser.parse_args()
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
    options = {'guarded_process_identity':args.guarded_process_identity}
    if args.guarded_query_worker: options['guarded_query_worker'] = True
    if args.guarded_observation_worker: options['guarded_observation_worker'] = True
    if args.guarded_window_lifecycle: options['guarded_window_lifecycle'] = True
    if args.guarded_owned_process: options['guarded_owned_process'] = True
    create_server(json.loads(args.targets.read_text(encoding='utf-8')),
                  args.output_directory, display_name=args.display, session_mode=args.session_mode,
                  **options).run(transport='stdio')


if __name__ == '__main__':
    main()
