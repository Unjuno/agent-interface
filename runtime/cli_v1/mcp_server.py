"""Optional stdio MCP transport over the existing one-shot public API."""
import argparse
import asyncio
from copy import deepcopy
import json
from pathlib import Path
import threading
from typing import Literal
import uuid

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, ImageContent, TextContent
from pydantic import StrictBool, StrictInt, StrictStr

from .api import dispatch
from .observe import observe
from .review import present_result


def content(result, *, error=False):
    metadata = dict(result)
    image = metadata.pop('image', None)
    blocks = [TextContent(type='text', text=json.dumps(metadata, allow_nan=False))]
    if image is not None:
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
    server = FastMCP('Agent Interface public one-shot API', instructions=(
        'Configured target names: ' + json.dumps(sorted(targets)) + '. '
        'Each call owns one backend session. No source/lease is issued by this server. '
        'Caller supplies current observation and binding values. Inspect action, image and cleanup '
        'outcomes separately. Never replay an uncertain action automatically.'))

    def invoke(operation, kwargs, compact):
        try:
            call_root = root / uuid.uuid4().hex
            call_root.mkdir(exist_ok=False)
            # Serialize before calling the backend. A persistence failure here sends no input.
            request = {'operation': operation, 'arguments': kwargs, 'targets': targets,
                       'display_name': display_name}
            (call_root / 'request.json').write_text(
                json.dumps(request, allow_nan=False), encoding='utf-8')
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
            data = json.dumps(report, allow_nan=False).encode('utf-8')
            try:
                (call_root / 'report.json').write_bytes(data)
                persistence_error = None
            except OSError as error:
                persistence_error = repr(error)
            result = present_result(report, call_root, compact=compact)
            result['call_directory'] = str(call_root)
            if persistence_error is not None:
                result['persistence_error'] = persistence_error
            return content(result)
        finally:
            lock.release()

    async def submit(operation, kwargs, compact):
        # Decide busy before scheduling a worker; thread-pool contention must not queue input.
        if not lock.acquire(blocking=False):
            return content({'status': 'busy', 'operation_invoked': False}, error=True)
        worker = asyncio.create_task(asyncio.to_thread(invoke, operation, kwargs, compact))
        workers.add(worker)
        def finished(task):
            workers.discard(task)
            if not task.cancelled():
                task.exception()
        worker.add_done_callback(finished)
        # A cancelled transport must not cancel a queued worker and strand its lock.
        return await asyncio.shield(worker)

    @server.tool()
    async def interface_observe(target: StrictStr, frame: Literal['window_client', 'screen_physical_px'],
                          region: list[StrictInt], compact: StrictBool = False) -> CallToolResult:
        """Capture one explicit region without input; return receipt and native image block."""
        return await submit('observe', {'target': target, 'frame': frame, 'region': region}, compact)

    @server.tool()
    async def interface_dispatch(program: dict, current_observation_seq: StrictInt,
                           current_binding_revision: StrictInt,
                           compact: StrictBool = False) -> CallToolResult:
        """Dispatch once through core admission. Include observe for an image; no implicit replay.

        Sequence/binding values are caller assertions, not server-issued freshness.
        A returned image may precede redraw. Release and cleanup failures remain visible.
        """
        return await submit('dispatch', {'program': program,
            'current_observation_seq': current_observation_seq,
            'current_binding_revision': current_binding_revision}, compact)

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
