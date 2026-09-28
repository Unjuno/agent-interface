"""Optional stdio MCP transport; one-shot by default, explicit persistent X11 option."""
import argparse
import asyncio
from copy import deepcopy
from contextlib import asynccontextmanager
import json
from itertools import islice, dropwhile
from pathlib import Path
import threading
from typing import Annotated, Literal
import uuid

from mcp.server.fastmcp import FastMCP
import anyio
from mcp.types import CallToolResult, ImageContent, TextContent
from pydantic import Field, StrictBool, StrictInt, StrictStr

from .api import dispatch, dispatch_in_session
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
    'when input requires focus. Operation examples: {"op":"text","text":"abc","gap_ms":20}, '
    '{"op":"key_chord","keys":["Left"],"repeat":2}, '
    '{"op":"key_chord","keys":["CTRL","s"]}, '
    '{"op":"observe","frame":"window_client","x":0,"y":0,"w":400,"h":180}. '
    'Use the actual target and observed region; examples do not select them for you. '
    'End with exactly one {"op":"release_all"}. Expanded ops must fit 128. '
    'gap_ms is optional integer 0..1000; key_chord repeat is optional integer 1..126. '
    'Observation captures once and does not pause for a model decision. '
    'Before replacing field text, inspect the selection and resulting value before committing. '
    'Emitted clicks or CTRL+a are not acknowledgements that a widget has processed them. '
    'On X11, window_client uses target-client coordinates and may omit overlapping dialogs; '
    'screen_physical_px uses display coordinates and includes other visible windows in the explicit region. '
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


def present_management_report(report, call_root):
    row = dict(report)
    if 'observation_report' in report:
        shown = present_result(report['observation_report'], call_root)
        for key in ('image', 'image_status', 'image_error'):
            if key in shown:
                row[key] = shown[key]
    return row


def create_server(targets, output_directory, *, display_name=None, session_mode="one-shot"):
    if session_mode not in ("one-shot", "persistent-x11", "guarded-x11"):
        raise ValueError("unknown session mode")
    if (not isinstance(targets, dict) or not targets or
            any(not isinstance(k, str) or not k or type(v) is not int or v <= 0
                for k, v in targets.items())):
        raise ValueError('explicit nonempty target name -> positive native ID mapping required')
    targets = deepcopy(targets)
    root = Path(output_directory).resolve()
    root.mkdir(parents=True, exist_ok=True)
    lock = threading.Lock()
    workers = set()
    calls = {}
    calls_lock = threading.Lock()
    owner = MCPSessionOwner(targets, display_name) if session_mode == 'persistent-x11' else None
    guarded = session_mode == 'guarded-x11'
    if guarded:
        from .mcp_guarded import GuardedSessionOwner
        owner = GuardedSessionOwner(targets, root, display_name)
    shutting_down = False

    def close_owner():
        report = owner.close()
        _write_json(root / ('session-' + owner.session_id + '-close.json'), report)
        return report

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
                if workers:
                    await asyncio.gather(*list(workers), return_exceptions=True)
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

    def invoke(operation, kwargs, compact, report_refs, detail="full", observation_refs=False):
        call_id = None
        try:
            call_root = root / uuid.uuid4().hex
            call_root.mkdir(exist_ok=False)
            call_id = call_root.name
            with calls_lock:
                calls[call_id] = {"call_id": call_id, "operation": operation,
                                  "state": "running", "arguments": deepcopy(kwargs),
                                  "backend_attempted": False, "persistence_failure": None}
            # Serialize before calling the backend. A persistence failure here sends no input.
            request = {'operation': operation, 'arguments': kwargs, 'targets': deepcopy(owner.targets) if owner else targets,
                       'display_name': display_name}
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
            # Attempt boundary only, not proof that the backend emitted input.
            with calls_lock:
                calls[call_id]['backend_attempted'] = True
            try:
                if operation == 'close':
                    report = close_owner()
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
                    session = owner.get()
                    options.pop('display_name')
                    if operation == 'observe':
                        report = observe_in_session(session, **options)
                    elif options['current_binding_revision'] != owner.binding_revision:
                        report = {'status': 'invalid_request', 'error': 'SESSION_BINDING_REVISION_MISMATCH',
                                  'input_dispatched': False, 'operation_invoked': False}
                    else:
                        owner.dispatch_attempted = True
                        program = options.pop('program')
                        report = dispatch_in_session(session, program, **options)
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
                if owner is not None and owner.state == 'failed' and owner.session is None:
                    report.update(status='backend_unavailable', failure_phase='session_initialization',
                                  operation_invoked=False, input_dispatched=False, effect_status='none')
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
            result = (present_management_report(report, call_root) if (operation.startswith('guarded_') or operation in ('close', 'inspect_target', 'review_target')) else
                      present_result(report, call_root, compact=compact, report_refs=report_refs))
            if owner is not None:
                result['session'] = owner.snapshot()
            result['call_directory'] = str(call_root)
            result['call_id'] = call_id
            if persistence_error is not None:
                result['persistence_error'] = persistence_error
                result['replay_allowed'] = False
            if detail == 'brief':
                from .guarded_presentation import brief_guarded_report
                result = brief_guarded_report(result)
            if observation_refs and operation.startswith('guarded_'):
                from .receipt_references import compact_guarded_observation
                result = compact_guarded_observation(result)
            return content(result, error=persistence_error is not None or (
                (operation.startswith('guarded_') or operation in ('close', 'inspect_target', 'review_target')) and
                (report.get('error') is not None or report.get('status') in ('cleanup_failed','refused','needs_review')
                 or report.get('feedback_status') == 'observation_failed')))
        finally:
            if call_id is not None:
                with calls_lock:
                    calls[call_id]["state"] = "finished"
            lock.release()

    async def submit(operation, kwargs, compact, report_refs, detail="full", observation_refs=False):
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
        worker = asyncio.create_task(asyncio.to_thread(invoke, operation, kwargs, compact, report_refs, detail, observation_refs))
        workers.add(worker)
        def finished(task):
            workers.discard(task)
            if not task.cancelled():
                task.exception()
        worker.add_done_callback(finished)
        # A cancelled transport must not cancel a queued worker and strand its lock.
        return await asyncio.shield(worker)

    if owner is not None and not guarded:
        @server.tool()
        async def interface_inspect_target(target: StrictStr,
                                           screen_region: list[StrictInt] | None = None) -> CallToolResult:
            """Read the focused managed client in this target's configured transient family.

            Does not select, focus or send input. Returns a one-use 30s review ID.
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
        register_guarded_tools(server, submit)
    else:
        @server.tool()
        async def interface_observe(target: StrictStr, frame: Literal['window_client', 'screen_physical_px'],
                              region: list[StrictInt], compact: StrictBool = False, report_refs: StrictBool = False) -> CallToolResult:
            """Capture once without input; return receipt and native image block.

            Region is [x, y, width, height]. On X11, window_client coordinates are
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
                               compact: StrictBool = False, report_refs: StrictBool = False) -> CallToolResult:
            """Dispatch once through core admission. Include observe for an image; no implicit replay.

            Observation sequence is a caller assertion, not server-issued freshness.
            Persistent mode requires session.binding_revision (initially 1); review
            advances it. One-shot binding values remain caller assertions.
            A returned image may precede redraw. Release and cleanup failures remain visible.
            report_refs requires compact=true and a v3 receipt decoder.
            In v3, read the full report at receipt.source.raw_report in this response;
            the report reference requires no additional tool call.
            """
            return await submit('dispatch', {'program': program,
                'current_observation_seq': current_observation_seq,
                'current_binding_revision': current_binding_revision}, compact, report_refs)

    @server.tool()
    async def interface_results(call_id: StrictStr | None = None,
                                before_call_id: StrictStr | None = None,
                                compact: StrictBool = False,
                                include_image: StrictBool = True,
                                report_refs: StrictBool = False,
                                detail: Literal["full", "brief"] = "full",
                                observation_refs: StrictBool = False) -> CallToolResult:
        """List this server's calls or reread one retained result. Never dispatch or observe.

        A finished worker is not proof of task success. Unknown calls are not replayed.
        This registry lasts only for this server process; no restart recovery is implied.
        Set include_image=false to inspect metadata without resending a retained image.
        detail=brief projects only normal guarded-input checks; full is the default.
        Critical/unsupported guarded reports stay full; other modes are unchanged.
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
            return content({'status': 'pending', 'call': record, 'operation_invoked': False})
        call_root = root / call_id  # Only IDs minted and held by this server are accepted.
        try:
            report = json.loads(await asyncio.to_thread((call_root / 'report.json').read_text,
                                                       encoding='utf-8'))
        except (OSError, ValueError) as error:
            return content({'status': 'receipt_unavailable', 'call': record,
                'error': repr(error), 'operation_invoked': False,
                'replay_allowed': False}, error=True)
        result = (await asyncio.to_thread(present_management_report, report, call_root) if (record['operation'].startswith('guarded_') or record['operation'] in ('close', 'inspect_target', 'review_target')) else
                  await asyncio.to_thread(present_result, report, call_root, compact=compact, report_refs=report_refs))
        result.update(call_id=call_id, call_directory=str(call_root), retained_call=record,
                      operation_invoked=False)
        if detail == 'brief' and record['operation'].startswith('guarded_'):
            from .guarded_presentation import brief_guarded_report
            result = brief_guarded_report(result)
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
    args = parser.parse_args()
    create_server(json.loads(args.targets.read_text(encoding='utf-8')),
                  args.output_directory, display_name=args.display, session_mode=args.session_mode).run(transport='stdio')


if __name__ == '__main__':
    main()
