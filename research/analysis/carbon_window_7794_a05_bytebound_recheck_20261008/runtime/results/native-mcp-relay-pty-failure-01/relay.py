"""Sequential JSON-lines relay to one native MCP server; never chooses/retries input."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class Relay:
    def __init__(self, client):
        self.client = client
        self.next_id = 1

    async def request(self, line):
        try:
            request = json.loads(line, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
            if not isinstance(request, dict) or set(request) != {'id', 'tool', 'arguments'}:
                raise ValueError('exact id/tool/arguments envelope required')
            if type(request['id']) is not int or request['id'] != self.next_id:
                raise ValueError(f'next id must be {self.next_id}; never resend an accepted id')
            if request['tool'] not in ('list_tools', 'native_start', 'native_status',
                                       'native_observe', 'native_submit', 'native_resume'):
                raise ValueError('unknown native relay tool')
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


async def main(server_args):
    parameters = StdioServerParameters(command=sys.executable,
        args=[str(Path(__file__).with_name('native_mcp_v1.py')), *server_args], env=dict(os.environ))
    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer) as client:
            await client.initialize()
            relay = Relay(client)
            while True:
                line = await asyncio.to_thread(sys.stdin.readline)
                if not line:
                    break  # Disconnect is not a finish request or a cleanup guarantee.
                response = await relay.request(line)
                print(json.dumps(response, allow_nan=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('server_args', nargs=argparse.REMAINDER,
                        help='after --, explicit native_mcp_v1 server arguments')
    args = parser.parse_args().server_args
    if args[:1] == ['--']:
        args = args[1:]
    if not args:
        parser.error('explicit native server arguments required')
    asyncio.run(main(args))
