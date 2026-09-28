"""Sequential JSON-lines relay to one explicitly selected MCP server; never chooses/retries input."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


NATIVE_TOOLS = ('list_tools', 'native_start', 'native_status', 'native_observe',
                'native_submit', 'native_resume', 'native_stop')
PUBLIC_TOOLS = ('list_tools', 'interface_validate', 'interface_observe', 'interface_dispatch',
                'interface_results', 'interface_inspect_target', 'interface_review_target',
                'interface_close', 'interface_guarded_observe', 'interface_guarded_mint',
                'interface_guarded_input', 'interface_guarded_review_window')


class Relay:
    def __init__(self, client, *, tools=NATIVE_TOOLS):
        self.client = client
        self.tools = tools
        self.next_id = 1

    async def request(self, line):
        try:
            request = json.loads(line, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
            if not isinstance(request, dict) or set(request) != {'id', 'tool', 'arguments'}:
                raise ValueError('exact id/tool/arguments envelope required')
            if type(request['id']) is not int or request['id'] != self.next_id:
                raise ValueError(f'next id must be {self.next_id}; never resend an accepted id')
            if request['tool'] not in self.tools:
                raise ValueError('unknown relay tool for selected server kind')
            if not isinstance(request['arguments'], dict):
                raise ValueError('arguments object required')
            if request['tool'] == 'list_tools' and request['arguments']:
                raise ValueError('list_tools takes empty arguments')
        except (ValueError, TypeError) as error:
            return {'status':'refused', 'dispatched':False, 'next_id':self.next_id, 'error':str(error)}
        self.next_id += 1  # Consume before dispatch, including ambiguous failures.
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


async def main(server_args, *, server_kind='native', runtime_archive=None):
    if server_kind == 'public':
        launch = ([str(Path(runtime_archive).resolve(strict=True)), 'mcp'] if runtime_archive else
                  ['-m', 'runtime.cli_v1.mcp_server'])
        tools = PUBLIC_TOOLS
    elif server_kind == 'native' and runtime_archive is None:
        launch = [str(Path(__file__).with_name('native_mcp_v1.py'))]
        tools = NATIVE_TOOLS
    else:
        raise ValueError('runtime archive requires public server kind')
    parameters = StdioServerParameters(command=sys.executable,
        args=[*launch, *server_args], env=dict(os.environ))
    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer) as client:
            await client.initialize()
            relay = Relay(client, tools=tools)
            while True:
                line = await asyncio.to_thread(sys.stdin.readline)
                if not line:
                    break  # Disconnect is not a finish request or a cleanup guarantee.
                response = await relay.request(line)
                print(json.dumps(response, allow_nan=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server-kind', choices=('native','public'), default='native')
    parser.add_argument('--runtime-archive', type=Path, help='explicit portable public runtime archive')
    parser.add_argument('server_args', nargs=argparse.REMAINDER,
                        help='after --, explicit arguments for the selected server')
    options = parser.parse_args()
    args = options.server_args
    if args[:1] == ['--']:
        args = args[1:]
    if not args:
        parser.error('explicit native server arguments required')
    if sys.stdout.isatty():
        parser.error('relay stdout must be a pipe or file, not a terminal; image JSON must remain byte-exact')
    asyncio.run(main(args, server_kind=options.server_kind, runtime_archive=options.runtime_archive))
