"""Ordinary decoder repair characterization using an inert SDK-shaped client."""
import asyncio
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from mcp.types import CallToolResult


class Client:
    def __init__(self):
        self.calls = []

    async def call_tool(self, tool, arguments):
        self.calls.append({'tool': tool, 'arguments': arguments})
        return CallToolResult(content=[])


async def main():
    root = Path(__file__).resolve().parent
    cases = json.loads((root / 'cases.json').read_bytes())
    started = datetime.now(timezone.utc).isoformat()
    rows = []
    for variant in ('baseline', 'candidate'):
        source = root / 'source' / (variant + '_relay.py')
        spec = importlib.util.spec_from_file_location('duplicate_probe_' + variant, source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for case in cases:
            client = Client()
            relay = module.Relay(client)
            response = await relay.request(case['line'])
            initial_calls = list(client.calls)
            followup = await relay.request('{"id":1,"tool":"interface_dispatch","arguments":{}}')
            rows.append({'variant': variant, 'case': case['name'], 'line': case['line'],
                         'response': response, 'initial_calls': initial_calls,
                         'initial_call_count': len(initial_calls),
                         'same_id_followup': followup, 'final_calls': client.calls,
                         'final_call_count': len(client.calls)})
    result = {'schema': 'relay-duplicate-json-construction-v1',
              'started_at': started, 'ended_at': datetime.now(timezone.utc).isoformat(),
              'python': sys.version, 'platform': platform.platform(),
              'mcp': importlib.metadata.version('mcp'),
              'sources': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted((root / 'source').glob('*.py'))},
              'cases_sha256': hashlib.sha256((root / 'cases.json').read_bytes()).hexdigest(),
              'rows': rows}
    with (root / 'raw.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, allow_nan=False, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps({'rows': len(rows), 'raw_sha256': hashlib.sha256((root / 'raw.json').read_bytes()).hexdigest()}))


if __name__ == '__main__':
    asyncio.run(main())
