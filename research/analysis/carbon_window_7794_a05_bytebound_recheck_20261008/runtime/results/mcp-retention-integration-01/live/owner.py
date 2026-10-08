import asyncio
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from Xlib.display import Display
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

root = Path('/out')
def save(name, value):
    (root/name).write_text(json.dumps(value, indent=2), encoding='utf-8')

async def run():
    params = StdioServerParameters(command=sys.executable, args=[
        '-m', 'runtime.cli_v1.mcp_server', '--targets', '/out/targets.json',
        '--output-directory', '/out/calls', '--display', ':88'],
        env=dict(os.environ, PYTHONPATH='/src', PYTHONDONTWRITEBYTECODE='1'))
    with (root/'server-stderr.log').open('w') as err:
        async with stdio_client(params, errlog=err) as (reader, writer):
            async with ClientSession(reader, writer) as client:
                await client.initialize()
                save('tools.json', (await client.list_tools()).model_dump(mode='json'))
                async def call(label, name, args):
                    save(label+'-request.json', {'tool': name, 'arguments': args})
                    start = time.monotonic_ns()
                    result = await client.call_tool(name, args)
                    save(label+'-timing.json', {'started_ns': start, 'ended_ns': time.monotonic_ns()})
                    save(label+'-response.json', result.model_dump(mode='json'))
                    for block in result.content:
                        if block.type == 'image':
                            (root/(label+'.png')).write_bytes(base64.b64decode(block.data))
                        elif block.type == 'text':
                            save(label+'-metadata.json', json.loads(block.text))
                    print(label+' ready', flush=True)
                await call('initial', 'interface_observe', {'target': 'fixture',
                    'frame': 'window_client', 'region': [0, 0, 400, 180], 'compact': True})
                for stage in range(1, 5):
                    path = root/f'decision-{stage}.json'
                    deadline = time.monotonic()+300
                    while not path.exists() and not (root/'finish').exists():
                        if time.monotonic()>deadline:
                            raise TimeoutError('primary decision deadline')
                        await asyncio.sleep(.1)
                    if (root/'finish').exists():
                        break
                    decision = json.loads(path.read_text())
                    name, args = decision['tool'], decision['arguments']
                    if name == 'interface_dispatch':
                        args['program']['authority']['expires_at_ns'] = time.monotonic_ns()+10_000_000_000
                    if name not in {'interface_validate', 'interface_dispatch', 'interface_results', 'interface_observe'}:
                        raise ValueError('unsupported tool')
                    await call(f'action-{stage}', name, args)

children = []
try:
    os.environ['DISPLAY'] = ':88'
    os.environ['XAUTHORITY'] = '/tmp/empty.auth'
    Path('/tmp/empty.auth').touch()
    with (root/'process.log').open('wb') as log:
        children.append(subprocess.Popen(['Xvfb', ':88', '-screen', '0', '1024x768x24',
            '-ac', '-nolisten', 'tcp', '-noreset'], stdout=log, stderr=log))
        deadline = time.monotonic()+10
        while True:
            try:
                connection = Display(':88'); connection.close(); break
            except Exception:
                if time.monotonic()>deadline: raise
                time.sleep(.05)
        children.append(subprocess.Popen(['/usr/bin/python3', '-m', 'runtime.backends.x11_v1.fixture_app',
            '--meta', '/out/meta.json', '--effect', '/out/effect.json'], stdout=log, stderr=log))
        deadline = time.monotonic()+10
        while not (root/'meta.json').exists():
            if time.monotonic()>deadline: raise TimeoutError('fixture readiness')
            time.sleep(.05)
        save('targets.json', {'fixture': json.loads((root/'meta.json').read_text())['window_id']})
        asyncio.run(run())
finally:
    states = []
    for child in reversed(children):
        if child.poll() is None: child.terminate()
        try: child.wait(timeout=5)
        except subprocess.TimeoutExpired: child.kill(); child.wait()
        states.append({'pid': child.pid, 'exit_code': child.returncode})
    save('cleanup.json', states)
    print('owner finished', flush=True)
