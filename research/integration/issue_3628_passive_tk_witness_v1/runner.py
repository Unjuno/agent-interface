"""One isolated public MCP observe -> dispatch -> observe allocation."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time
import uuid

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_reply(root: Path, name: str, reply) -> dict:
    texts = [block.text for block in reply.content if block.type == 'text']
    images = [block for block in reply.content if block.type == 'image']
    image_rows = []
    for index, block in enumerate(images):
        data = base64.b64decode(block.data, validate=True)
        path = root / f'{name}-{index:02d}.png'
        path.write_bytes(data)
        image_rows.append({'path': path.name, 'mime_type': block.mimeType,
                           'bytes': len(data), 'sha256': digest(data),
                           'png_signature': data.startswith(b'\x89PNG\r\n\x1a\n')})
    text_path = root / f'{name}-text.json'
    parsed = json.loads(texts[0]) if len(texts) == 1 else None
    text_path.write_text(json.dumps(parsed, indent=2, sort_keys=True) + '\n')
    return {'text_path': text_path.name, 'text_count': len(texts),
            'is_error': bool(reply.isError), 'images': image_rows,
            'metadata': parsed}


async def main() -> None:
    root = Path('/evidence')
    root.mkdir(parents=True, exist_ok=True)
    work = Path('/tmp/isolated-client-workdir')
    work.mkdir(exist_ok=False)
    display = ':93'
    os.environ['DISPLAY'] = display
    xlog = (root / 'xvfb.log').open('wb')
    xproc = subprocess.Popen(['Xvfb', display, '-screen', '0', '800x600x24', '-nolisten', 'tcp'],
                             stdout=xlog, stderr=subprocess.STDOUT)
    fixture = None
    fixture_log = None
    data = {'schema': 'agent-interface/issue-3587-allocation-v1',
            'allocation_id': 'formal-' + uuid.uuid4().hex[:12],
            'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'container_image_id': os.environ.get('OBSTAC_IMAGE_ID'),
            'container_platform': os.environ.get('OBSTAC_PLATFORM'),
            'display': display, 'xvfb_pid': xproc.pid}
    try:
        deadline = time.monotonic() + 8
        socket = Path(f'/tmp/.X11-unix/X{display[1:]}')
        while time.monotonic() < deadline and not socket.exists():
            if xproc.poll() is not None:
                raise RuntimeError(f'Xvfb exited early: {xproc.returncode}')
            await asyncio.sleep(.05)
        if not socket.exists():
            raise TimeoutError('Xvfb socket readiness timeout')
        meta, effect, events = root/'fixture-meta.json', root/'fixture-effect.json', root/'fixture-events.jsonl'
        fixture_log = (root/'fixture.log').open('wb')
        fixture_env = {'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
                       'PYTHONPATH': '/source', 'PYTHONDONTWRITEBYTECODE': '1', 'DISPLAY': display}
        fixture = subprocess.Popen([
            sys.executable, '-m', 'runtime.backends.x11_v1.fixture_app',
            '--meta', str(meta), '--effect', str(effect), '--events', str(events)],
            cwd=work, env=fixture_env, stdout=subprocess.DEVNULL, stderr=fixture_log)
        data['fixture_pid'] = fixture.pid
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and not meta.exists():
            if fixture.poll() is not None:
                raise RuntimeError(f'fixture exited early: {fixture.returncode}')
            await asyncio.sleep(.05)
        if not meta.exists():
            raise TimeoutError('fixture readiness timeout')
        wid = json.loads(meta.read_text())['window_id']
        data['window_id'] = wid
        targets = root/'targets.json'
        targets.write_text(json.dumps({'fixture': wid}, sort_keys=True) + '\n')
        marker = 'orb3587-' + uuid.uuid4().hex[:12]
        data['marker'] = marker
        archive = Path('/artifact/agent-interface-runtime.pyz')
        artifact_bytes = archive.read_bytes()
        data['artifact_sha256'] = digest(artifact_bytes)
        import zipfile
        with zipfile.ZipFile(archive) as zf:
            data['build_metadata'] = json.loads(zf.read('BUILD.json'))
        client_env = {'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
                      'HOME': '/tmp/empty-home', 'PYTHONDONTWRITEBYTECODE': '1', 'DISPLAY': display}
        Path(client_env['HOME']).mkdir()
        params = StdioServerParameters(command=sys.executable, cwd=str(work), args=[
            str(archive), 'mcp', '--targets', str(targets),
            '--output-directory', str(root/'calls'), '--display', display], env=client_env)
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as client:
                await client.initialize()
                listed = await client.list_tools()
                data['listed_tools'] = sorted(tool.name for tool in listed.tools)
                first = await client.call_tool('interface_observe', {
                    'target': 'fixture', 'frame': 'window_client', 'region': [0, 0, 400, 180]})
                data['initial_observation'] = save_reply(root, 'initial', first)
                program = {
                    'schema': 'agent-interface/program-v1', 'program_id': 'orb3587-program',
                    'source': {'observation_seq': 0, 'binding_revision': 0},
                    'authority': {'lease_id': 'orb3587-single-use',
                                  'expires_at_ns': time.monotonic_ns() + 20_000_000_000},
                    'terminal': {'release_all_required': True},
                    'ops': [
                        {'op': 'focus', 'target': 'fixture'},
                        {'op': 'pointer_move', 'frame': 'window_client', 'x': 70, 'y': 55},
                        {'op': 'pointer_button', 'button': 'left', 'down': True},
                        {'op': 'pointer_button', 'button': 'left', 'down': False},
                        {'op': 'text', 'text': marker},
                        {'op': 'key_chord', 'keys': ['CTRL', 'S']},
                        {'op': 'wait_update', 'timeout_ms': 100},
                        {'op': 'observe', 'frame': 'window_client', 'x': 0, 'y': 0,
                         'w': 400, 'h': 180},
                        {'op': 'release_all'}]}
                data['program'] = program
                action = await client.call_tool('interface_dispatch', {
                    'program': program, 'current_observation_seq': 0,
                    'current_binding_revision': 0})
                data['dispatch'] = save_reply(root, 'dispatch', action)
                # This distinct read-only continuation is after the action response.
                post = await client.call_tool('interface_observe', {
                    'target': 'fixture', 'frame': 'window_client', 'region': [0, 0, 400, 180]})
                data['post_observation'] = save_reply(root, 'post', post)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline and not effect.exists():
            await asyncio.sleep(.05)
        data['effect'] = json.loads(effect.read_text()) if effect.exists() else None
        data['fixture_events'] = events.read_text().splitlines() if events.exists() else []
        call_root = root/'calls'
        requests = sorted(call_root.glob('*/request.json'))
        reports = sorted(call_root.glob('*/report.json'))
        data['request_count'] = len(requests)
        data['report_count'] = len(reports)
        data['call_records'] = []
        ordered_call_ids = [Path(data[key]['metadata']['call_directory']).name
                            for key in ('initial_observation', 'dispatch', 'post_observation')]
        for call_id in ordered_call_ids:
            path = call_root/call_id/'request.json'
            row = json.loads(path.read_text())
            data['call_records'].append({'call_id': path.parent.name, 'operation': row['operation'],
                'request_sha256': digest(path.read_bytes()),
                'report_sha256': digest((path.parent/'report.json').read_bytes())
                    if (path.parent/'report.json').exists() else None,
                'request': row,
                'report': json.loads((path.parent/'report.json').read_text())
                    if (path.parent/'report.json').exists() else None})
        data['runtime'] = {'python': sys.version, 'platform': platform.platform(),
            'mcp': importlib.metadata.version('mcp'),
            'python_xlib': importlib.metadata.version('python-xlib'),
            'pillow': importlib.metadata.version('Pillow')}
    except BaseException as error:
        data['runner_error'] = repr(error)
        raise
    finally:
        if fixture is not None and fixture.poll() is None:
            fixture.terminate()
            try:
                fixture.wait(timeout=3)
            except subprocess.TimeoutExpired:
                fixture.kill(); fixture.wait(timeout=3)
        data['fixture_exit_code'] = None if fixture is None else fixture.returncode
        if xproc.poll() is None:
            xproc.terminate()
        try:
            xproc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            xproc.kill(); xproc.wait(timeout=3)
        data['xvfb_exit_code'] = xproc.returncode
        data['x11_socket_removed'] = not Path(f'/tmp/.X11-unix/X{display[1:]}').exists()
        data['children_reaped'] = ((fixture is None or fixture.poll() is not None) and xproc.poll() is not None)
        (root/'allocation.json').write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
        if fixture_log is not None:
            fixture_log.close()
        xlog.close()


if __name__ == '__main__':
    asyncio.run(main())
