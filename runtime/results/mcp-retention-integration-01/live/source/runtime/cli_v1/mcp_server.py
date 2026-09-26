"""Optional stdio MCP transport over the existing one-shot public API."""
import argparse
import asyncio
from copy import deepcopy
import json
from itertools import islice, dropwhile
from pathlib import Path
import threading
from typing import Annotated, Literal
import uuid

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, ImageContent, TextContent
from pydantic import Field, StrictBool, StrictInt, StrictStr

from .api import dispatch
from .attempt import _write_json
from .observe import observe
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


def create_server(targets, output_directory, *, display_name=None):
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
    server = FastMCP('Agent Interface public one-shot API', instructions=(
        'Configured target names: ' + json.dumps(sorted(targets)) + '. '
        'Each call owns one backend session. No source/lease is issued by this server. '
        'Caller supplies current observation and binding values. Inspect action, image and cleanup '
        'outcomes separately. Never replay an uncertain action automatically.'))

    def invoke(operation, kwargs, compact, report_refs):
        call_id = None
        try:
            call_root = root / uuid.uuid4().hex
            call_root.mkdir(exist_ok=False)
            call_id = call_root.name
            with calls_lock:
                calls[call_id] = {"call_id": call_id, "operation": operation,
                                  "state": "running", "arguments": deepcopy(kwargs)}
            # Serialize before calling the backend. A persistence failure here sends no input.
            request = {'operation': operation, 'arguments': kwargs, 'targets': targets,
                       'display_name': display_name}
            try:
                _write_json(call_root / 'request.json', request)
            except (OSError, ValueError, TypeError) as error:
                return content({'status': 'invalid_request',
                    'error': 'REQUEST_PERSISTENCE_FAILED', 'detail': repr(error),
                    'failure_phase': 'request_persistence', 'operation_invoked': False,
                    'call_id': call_id, 'call_directory': str(call_root),
                    'replay_allowed': False}, error=True)
            options = dict(kwargs, capture_directory=str(call_root / 'images'),
                           display_name=display_name)
            try:
                if operation == 'observe':
                    report = observe(deepcopy(targets), **options)
                else:
                    program = options.pop('program')
                    report = dispatch(program, deepcopy(targets), **options)
            except Exception as error:
                # The call may already have emitted input. Never retry to recover a receipt.
                report = {'status': 'runtime_failed', 'error': repr(error),
                          'operation': operation, 'operation_invoked': True,
                          'effect_status': 'unknown'}
            try:
                _write_json(call_root / 'report.json', report)
                persistence_error = None
            except OSError as error:
                persistence_error = repr(error)
            result = present_result(report, call_root, compact=compact, report_refs=report_refs)
            result['call_directory'] = str(call_root)
            result['call_id'] = call_id
            if persistence_error is not None:
                result['persistence_error'] = persistence_error
                result['replay_allowed'] = False
            return content(result, error=persistence_error is not None)
        finally:
            if call_id is not None:
                with calls_lock:
                    calls[call_id]["state"] = "finished"
            lock.release()

    async def submit(operation, kwargs, compact, report_refs):
        if report_refs and not compact:
            return content({'status': 'invalid_request',
                'error': 'report_refs requires compact=true',
                'operation_invoked': False}, error=True)
        # Decide busy before scheduling a worker; thread-pool contention must not queue input.
        if not lock.acquire(blocking=False):
            return content({'status': 'busy', 'operation_invoked': False}, error=True)
        worker = asyncio.create_task(asyncio.to_thread(invoke, operation, kwargs, compact, report_refs))
        workers.add(worker)
        def finished(task):
            workers.discard(task)
            if not task.cancelled():
                task.exception()
        worker.add_done_callback(finished)
        # A cancelled transport must not cancel a queued worker and strand its lock.
        return await asyncio.shield(worker)

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
        """
        return await submit('observe', {'target': target, 'frame': frame, 'region': region}, compact, report_refs)

    @server.tool()
    async def interface_dispatch(program: PublicProgram, current_observation_seq: StrictInt,
                           current_binding_revision: StrictInt,
                           compact: StrictBool = False, report_refs: StrictBool = False) -> CallToolResult:
        """Dispatch once through core admission. Include observe for an image; no implicit replay.

        Sequence/binding values are caller assertions, not server-issued freshness.
        A returned image may precede redraw. Release and cleanup failures remain visible.
        report_refs requires compact=true and a v3 receipt decoder.
        """
        return await submit('dispatch', {'program': program,
            'current_observation_seq': current_observation_seq,
            'current_binding_revision': current_binding_revision}, compact, report_refs)

    @server.tool()
    async def interface_results(call_id: StrictStr | None = None,
                                before_call_id: StrictStr | None = None,
                                compact: StrictBool = False,
                                include_image: StrictBool = True,
                                report_refs: StrictBool = False) -> CallToolResult:
        """List this server's calls or reread one retained result. Never dispatch or observe.

        A finished worker is not proof of task success. Unknown calls are not replayed.
        This registry lasts only for this server process; no restart recovery is implied.
        Set include_image=false to inspect metadata without resending a retained image.
        report_refs requires compact=true and a v3 receipt decoder.
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
                'error': repr(error), 'operation_invoked': False}, error=True)
        result = await asyncio.to_thread(present_result, report, call_root, compact=compact, report_refs=report_refs)
        result.update(call_id=call_id, call_directory=str(call_root), retained_call=record,
                      operation_invoked=False)
        return content(result, include_image=include_image)

    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--targets', type=Path, required=True)
    parser.add_argument('--output-directory', type=Path, required=True)
    parser.add_argument('--display')
    args = parser.parse_args()
    create_server(json.loads(args.targets.read_text(encoding='utf-8')),
                  args.output_directory, display_name=args.display).run(transport='stdio')


if __name__ == '__main__':
    main()
