"""One bounded portable-zipapp MCP exchange against a private Tk fixture."""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
import platform
import importlib.metadata
import signal

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    root = Path('/evidence')
    root.mkdir(parents=True, exist_ok=True)
    work = Path('/tmp/isolated-client-workdir')
    work.mkdir(exist_ok=False)
    display = ':93'
    os.environ['DISPLAY'] = display
    xproc = subprocess.Popen(['Xvfb', display, '-screen', '0', '800x600x24', '-nolisten', 'tcp'],
                             stdout=(root/'xvfb.stdout').open('wb'), stderr=(root/'xvfb.stderr').open('wb'))
    fixture = None
    server = None
    try:
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and not Path(f'/tmp/.X11-unix/X{display[1:]}').exists():
            if xproc.poll() is not None:
                raise RuntimeError('Xvfb exited before display socket appeared')
            await asyncio.sleep(.05)
        if not Path(f'/tmp/.X11-unix/X{display[1:]}').exists():
            raise TimeoutError('Xvfb readiness timeout')
        meta, effect, events = root/'fixture-meta.json', root/'fixture-effect.json', root/'fixture-events.jsonl'
        fixture_log = (root/'fixture.stderr').open('wb')
        fixture_env = {'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
                       'PYTHONPATH': '/source', 'PYTHONDONTWRITEBYTECODE': '1', 'DISPLAY': display}
        fixture = subprocess.Popen([
            sys.executable, '-m', 'runtime.backends.x11_v1.fixture_app',
            '--meta', str(meta), '--effect', str(effect), '--events', str(events)],
            cwd=work, env=fixture_env, stdout=subprocess.DEVNULL,
            stderr=fixture_log)
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and not meta.exists():
            if fixture.poll() is not None:
                raise RuntimeError(f'fixture exited {fixture.returncode}')
            await asyncio.sleep(.05)
        if not meta.exists():
            raise TimeoutError('Tk fixture readiness timeout')
        wid = json.loads(meta.read_text())['window_id']
        targets = root/'targets.json'
        targets.write_text(json.dumps({'fixture': wid})+'\n')
        archive = Path('/artifact/agent-interface-runtime.pyz')
        archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
        env = {'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
               'HOME': '/tmp/empty-home', 'PYTHONDONTWRITEBYTECODE': '1', 'DISPLAY': display}
        Path(env['HOME']).mkdir()
        params = StdioServerParameters(command=sys.executable, cwd=str(work), args=[
            str(archive), 'mcp', '--targets', str(targets), '--output-directory', str(root/'calls'),
            '--display', display], env=env)
        transport_inits = 0
        observe_calls = 0
        dispatch_calls = 0
        marker = 'orb3573-' + uuid.uuid4().hex[:10]
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as client:
                await client.initialize()
                transport_inits += 1
                listed = await client.list_tools()
                names = sorted(tool.name for tool in listed.tools)
                observe = await client.call_tool('interface_observe', {
                    'target': 'fixture', 'frame': 'window_client', 'region': [0, 0, 400, 180]})
                observe_calls += 1
                observe_text = json.loads(observe.content[0].text)
                observe_images = [block for block in observe.content if block.type == 'image']
                program = {
                    'schema': 'agent-interface/program-v1', 'program_id': 'orb3573-program',
                    'source': {'observation_seq': 0, 'binding_revision': 0},
                    'authority': {'lease_id': 'orb3573-single-use',
                                  'expires_at_ns': time.monotonic_ns()+20_000_000_000},
                    'terminal': {'release_all_required': True},
                    'ops': [
                        {'op': 'focus', 'target': 'fixture'},
                        {'op': 'pointer_move', 'frame': 'window_client', 'x': 70, 'y': 55},
                        {'op': 'pointer_button', 'button': 'left', 'down': True},
                        {'op': 'pointer_button', 'button': 'left', 'down': False},
                        {'op': 'text', 'text': marker},
                        {'op': 'key_chord', 'keys': ['CTRL', 'S']},
                        {'op': 'wait_update', 'timeout_ms': 100},
                        {'op': 'observe', 'frame': 'window_client', 'x': 0, 'y': 0, 'w': 400, 'h': 180},
                        {'op': 'release_all'}]}
                dispatch = await client.call_tool('interface_dispatch', {
                    'program': program, 'current_observation_seq': 0,
                    'current_binding_revision': 0})
                dispatch_calls += 1
                dispatch_text = json.loads(dispatch.content[0].text)
                dispatch_images = [block for block in dispatch.content if block.type == 'image']
        # A fixture-side file is the independent application-effect oracle.
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline and not effect.exists():
            await asyncio.sleep(.05)
        calls = sorted((root/'calls').glob('*/report.json'))
        requests = sorted((root/'calls').glob('*/request.json'))
        report_rows = [json.loads(path.read_text()) for path in calls]
        dispatch_report = next((r for r in report_rows if r.get('schema') == 'agent-interface/runtime-dispatch-result-v1'), {})
        execution = dispatch_report.get('result', {}).get('execution', {})
        release_rows = execution.get('releases', [])
        png_hash = None
        if observe_images:
            import base64
            png_hash = hashlib.sha256(base64.b64decode(observe_images[0].data)).hexdigest()
        result = {
            'schema': 'agent-interface/issue-3573-container-result-v1',
            'transport_initialize_count': transport_inits, 'observe_call_count': observe_calls,
            'dispatch_call_count': dispatch_calls, 'listed_tools': names,
            'observation': {'text_status': observe_text.get('image_status'),
                            'image_block_count': len(observe_images), 'png_sha256': png_hash},
            'dispatch': {'text_status': dispatch_text.get('outcome_summary', {}).get('execution_status'),
                         'image_block_count': len(dispatch_images),
                         'release_rows': release_rows,
                         'image_status': dispatch_text.get('image_status')},
            'call_directory_count': len({p.parent for p in calls}),
            'report_count': len(calls), 'request_count': len(requests),
            'effect': json.loads(effect.read_text()) if effect.exists() else None,
            'marker': marker, 'archive_sha256': archive_hash,
            'runtime': {'python': sys.version, 'platform': platform.platform(),
                        'mcp_version': importlib.metadata.version('mcp'),
                        'python_xlib_version': importlib.metadata.version('python-xlib'),
                        'pillow_version': importlib.metadata.version('Pillow')},
            'fixture_event_lines': len(events.read_text().splitlines()) if events.exists() else 0,
        }
        (root/'smoke-result.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
        fixture.send_signal(signal.SIGINT)
        fixture.wait(timeout=3)
        result['fixture_exit_code'] = fixture.returncode
        xproc.terminate()
        xproc.wait(timeout=3)
        result['xvfb_exit_code'] = xproc.returncode
        (root/'smoke-result.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    finally:
        if fixture is not None and fixture.poll() is None:
            fixture.terminate(); fixture.wait(timeout=3)
        if xproc.poll() is None:
            xproc.terminate(); xproc.wait(timeout=3)


if __name__ == '__main__':
    asyncio.run(main())
