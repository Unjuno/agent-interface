"""Sequential JSON-lines public MCP client; no research allocation, action policy or replay."""
import argparse
import asyncio
import json
import math
import os
from pathlib import Path
import sys
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PUBLIC_TOOLS = ('list_tools', 'interface_clock', 'interface_validate', 'interface_observe', 'interface_dispatch',
                'interface_results', 'interface_inspect_target', 'interface_review_target',
                'interface_close', 'interface_recover_input', 'interface_guarded_observe', 'interface_guarded_mint',
                'interface_guarded_input', 'interface_guarded_review_window', 'interface_guarded_mint_many', 'interface_guarded_activate_window')


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


class Relay:
    def __init__(self, client, *, tools=PUBLIC_TOOLS):
        self.client = client
        self.tools = tools
        self.next_id = 1

    async def request(self, line):
        try:
            if isinstance(line, (bytes, bytearray)):
                line = line.decode('utf-8')
            request = json.loads(line, object_pairs_hook=_unique_object, parse_float=_finite_float,
                                 parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
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
        except (ValueError, TypeError, RecursionError) as error:
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
            while True:
                # Pipe bytes use the protocol encoding, independently of locale.
                line = await asyncio.to_thread(getattr(sys.stdin, 'buffer', sys.stdin).readline)
                if not line:
                    break
                response = await relay.request(line)
                encoded = json.dumps(response, allow_nan=False) + '\n'
                if sys.stdout.write(encoded) != len(encoded):
                    raise OSError('INCOMPLETE_RELAY_STDOUT_WRITE')
                sys.stdout.flush()


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
