"""Sequential JSON-lines public MCP client; no research allocation, action policy or replay."""
import argparse
import asyncio
from collections import deque
import json
import math
import os
from pathlib import Path
import sys
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PUBLIC_TOOLS = ('list_tools', 'interface_clock', 'interface_validate', 'interface_observe', 'interface_dispatch',
                'interface_cancel', 'interface_results', 'interface_inspect_target', 'interface_review_target',
                'interface_close', 'interface_recover_input', 'interface_guarded_observe', 'interface_guarded_mint',
                'interface_guarded_input', 'interface_guarded_review_window', 'interface_guarded_mint_many',
                'interface_guarded_activate_window', 'interface_guarded_recover_input',
                'interface_guarded_cancel', 'interface_guarded_compiled')

MAX_PENDING_STDOUT_RESPONSES = 16
MAX_PENDING_CANCEL_RESPONSES = 1
# A cancellation may pass four valid queued requests; one extra ordinary line
# can be retained as the bounded probe that determines whether a cancel follows.
MAX_CANCEL_READAHEAD_LINES = 4
CANCELLATION_TOOLS = ('interface_cancel', 'interface_guarded_cancel')


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError('nonfinite JSON number')
    return number


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON object key')
        result[key] = value
    return result


def _unicode_scalars(value):
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, str):
            item.encode('utf-8')
        elif isinstance(item, dict):
            pending.extend(item.keys())
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)


class Relay:
    def __init__(self, client, *, tools=PUBLIC_TOOLS):
        self.client = client
        self.tools = tools
        self.next_id = 1
        self._priority_cancel_id = None

    def _parse_request(self, line, *, expected_id=None, priority_cancel_id=None):
        try:
            if isinstance(line, (bytes, bytearray)):
                line = line.decode('utf-8')
            request = json.loads(line, object_pairs_hook=_unique_object, parse_float=_finite_float,
                                 parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
            _unicode_scalars(request)
            if not isinstance(request, dict) or set(request) != {'id', 'tool', 'arguments'}:
                raise ValueError('exact id/tool/arguments envelope required')
            expected_sequence_id = self.next_id if expected_id is None else expected_id
            expected_id_match = (type(request['id']) is int
                and request['id'] == expected_sequence_id)
            priority_cancel = (priority_cancel_id is not None
                and request.get('tool') in CANCELLATION_TOOLS
                and type(request.get('id')) is int
                and request['id'] == priority_cancel_id
                and priority_cancel_id > self.next_id
                and self._priority_cancel_id is None)
            if type(request['id']) is not int or not (
                    expected_id_match or priority_cancel):
                raise ValueError(f'next id must be {expected_sequence_id}; never resend an accepted id')
            if request['tool'] not in self.tools:
                raise ValueError('unknown relay tool for selected server kind')
            if not isinstance(request['arguments'], dict):
                raise ValueError('arguments object required')
            if request['tool'] == 'list_tools' and request['arguments']:
                raise ValueError('list_tools takes empty arguments')
            return request
        except (ValueError, TypeError, RecursionError) as error:
            raise ValueError(str(error)) from error

    def is_cancellation_request(self, line, *, expected_id=None, priority_cancel_id=None):
        try:
            return self._parse_request(
                line, expected_id=expected_id,
                priority_cancel_id=priority_cancel_id)['tool'] in CANCELLATION_TOOLS
        except ValueError:
            return False

    def is_expected_request(self, line, *, expected_id=None):
        try:
            self._parse_request(line, expected_id=expected_id)
            return True
        except ValueError:
            return False

    async def request(self, line, *, priority_cancel_id=None):
        try:
            request = self._parse_request(line, priority_cancel_id=priority_cancel_id)
        except ValueError as error:
            return {'status':'refused', 'dispatched':False, 'next_id':self.next_id, 'error':str(error)}
        if request['id'] == self.next_id:
            self.next_id += 1
            if self._priority_cancel_id == self.next_id:
                self.next_id += 1
                self._priority_cancel_id = None
        else:
            # A single cancellation may overtake the one queued request being
            # inspected at the bounded stdout-response limit. The missing ID
            # remains next until that deferred request is consumed.
            self._priority_cancel_id = request['id']
        response = {'id':request['id'], 'tool':request['tool'], 'sdk_entry_ns':time.monotonic_ns()}
        try:
            result = (await self.client.list_tools() if request['tool']=='list_tools' else
                      await self.client.call_tool(request['tool'], request['arguments']))
            response.update(status='returned', sdk_return_ns=time.monotonic_ns(),
                            result=result.model_dump(mode='json'))
        except Exception as error:
            response.update(status='unknown_requires_reconciliation', sdk_error_ns=time.monotonic_ns(),
                            error=repr(error), recovery='Inspect the same allocation/request. Do not replay input.')
        response['next_id'] = self.next_id
        return response


async def serve(server_args):
    # A packaged relay always launches the MCP server from that same archive.
    # Source-module use remains available for development in a checkout.
    archive = getattr(__loader__, 'archive', None)
    launch = ([str(Path(archive).resolve(strict=True)), 'mcp'] if archive else
              ['-m', 'runtime.cli_v1.mcp_server'])
    parameters = StdioServerParameters(command=sys.executable,
        args=[*launch, *server_args], env=dict(os.environ))
    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer) as client:
            await client.initialize()
            relay = Relay(client)
            output_lock = asyncio.Lock()
            pending_writes = set()
            pending_cancel_writes = set()
            deferred_lines = deque()
            input_eof = False
            stream = getattr(sys.stdin, 'buffer', sys.stdin)
            input_task = None

            async def write_response(response):
                encoded = await asyncio.to_thread(json.dumps, response, allow_nan=False)
                encoded += '\n'

                def emit():
                    output = getattr(sys.stdout, 'buffer', None)
                    if output is not None:
                        wire = encoded.encode('utf-8')
                        written = output.write(wire)
                        sys.stdout.flush()
                        expected = len(wire)
                    else:
                        written = sys.stdout.write(encoded)
                        sys.stdout.flush()
                        expected = len(encoded)
                    if written != expected:
                        raise OSError('INCOMPLETE_RELAY_STDOUT_WRITE')

                async with output_lock:
                    await asyncio.to_thread(emit)

            while True:
                # JSON-lines pipes are UTF-8 bytes regardless of the locale text wrapper.
                completed = {task for task in pending_writes if task.done()}
                pending_writes.difference_update(completed)
                pending_cancel_writes.difference_update(completed)
                for task in completed:
                    await task

                # A cancellation tool may already have run while its JSON
                # response is still queued behind stdout. Do not dispatch
                # later tools until that response is written successfully;
                # otherwise a writer failure can hide the cancel result while
                # new input continues through the relay.
                if pending_cancel_writes:
                    done, _ = await asyncio.wait(
                        pending_writes, return_when=asyncio.FIRST_COMPLETED)
                    pending_writes.difference_update(done)
                    pending_cancel_writes.difference_update(done)
                    for task in done:
                        await task
                    continue

                line = None
                line_is_cancel = None
                priority_cancel_id = None
                pending_full = len(pending_writes) >= MAX_PENDING_STDOUT_RESPONSES
                cancel_slot_available = (
                    len(pending_cancel_writes) < MAX_PENDING_CANCEL_RESPONSES)
                if deferred_lines and not pending_full:
                    line = deferred_lines.popleft()
                elif pending_full and deferred_lines:
                    deferred_prefix_is_ordinary = all(
                        relay.is_expected_request(request_line,
                            expected_id=relay.next_id + index)
                        and not relay.is_cancellation_request(request_line,
                            expected_id=relay.next_id + index)
                        for index, request_line in enumerate(deferred_lines))
                    if (cancel_slot_available
                            and relay._priority_cancel_id is None
                            and len(deferred_lines) <= MAX_CANCEL_READAHEAD_LINES
                            and deferred_prefix_is_ordinary
                            and not input_eof):
                        if input_task is None:
                            input_task = asyncio.create_task(
                                asyncio.to_thread(stream.readline))
                        done, _ = await asyncio.wait(
                            {input_task, *pending_writes},
                            return_when=asyncio.FIRST_COMPLETED)
                        completed = done.intersection(pending_writes)
                        pending_writes.difference_update(completed)
                        pending_cancel_writes.difference_update(completed)
                        for task in completed:
                            await task
                        if input_task in done:
                            candidate = await input_task
                            input_task = None
                            if not candidate:
                                input_eof = True
                            else:
                                candidate_id = relay.next_id + len(deferred_lines)
                                candidate_priority_id = (candidate_id
                                    if deferred_lines else None)
                                if relay.is_cancellation_request(candidate,
                                        expected_id=candidate_id,
                                        priority_cancel_id=candidate_priority_id):
                                    line = candidate
                                    line_is_cancel = True
                                    priority_cancel_id = candidate_priority_id
                                else:
                                    deferred_lines.append(candidate)
                        if line is None:
                            continue
                    else:
                        done, _ = await asyncio.wait(
                            pending_writes, return_when=asyncio.FIRST_COMPLETED)
                        pending_writes.difference_update(done)
                        pending_cancel_writes.difference_update(done)
                        for task in done:
                            await task
                        continue
                elif input_eof:
                    break
                else:
                    if input_task is None:
                        input_task = asyncio.create_task(
                            asyncio.to_thread(stream.readline))
                    if pending_full:
                        done, _ = await asyncio.wait(
                            {input_task, *pending_writes},
                            return_when=asyncio.FIRST_COMPLETED)
                        completed = done.intersection(pending_writes)
                        pending_writes.difference_update(completed)
                        pending_cancel_writes.difference_update(completed)
                        for task in completed:
                            await task
                        if input_task not in done:
                            continue
                    line = await input_task
                    input_task = None
                if not line:
                    if deferred_lines:
                        input_eof = True
                        continue
                    break

                is_cancel = (line_is_cancel if line_is_cancel is not None
                             else relay.is_cancellation_request(line))
                if len(pending_writes) >= MAX_PENDING_STDOUT_RESPONSES and (
                        not is_cancel or len(pending_cancel_writes) >= MAX_PENDING_CANCEL_RESPONSES):
                    deferred_lines.append(line)
                    continue

                response = await relay.request(line, priority_cancel_id=priority_cancel_id)
                write_task = asyncio.create_task(write_response(response))
                pending_writes.add(write_task)
                if is_cancel:
                    pending_cancel_writes.add(write_task)
            if pending_writes:
                await asyncio.gather(*pending_writes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('server_args', nargs=argparse.REMAINDER,
                        help='after --, explicit public MCP server arguments')
    args = parser.parse_args().server_args
    if args[:1] == ['--']:args = args[1:]
    if not args:parser.error('explicit public server arguments required')
    if sys.stdout.isatty():
        parser.error('relay stdout must be a pipe or file, not a terminal; image JSON must remain byte-exact')
    asyncio.run(serve(args))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
