"""One persistent stdio client; pause after native image for model authorship."""
import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path
import sys
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


ROOT = Path('/evidence')
SERVER = '/workspace/research/live_control/native_mcp_v1.py'


def save_response(name, result):
    payload = result.model_dump(mode='json')
    (ROOT/name).write_text(json.dumps(payload, sort_keys=True)+'\n')
    images = []
    for index, block in enumerate(result.content):
        if block.type == 'image':
            data = base64.b64decode(block.data, validate=True)
            path = ROOT/f'{name.removesuffix(".json")}-image-{index}.png'
            path.write_bytes(data)
            images.append({'index': index, 'path': str(path), 'bytes': len(data)})
    return payload, images


async def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    tools_path = ROOT/'tools.json'
    params = StdioServerParameters(command='/opt/mcp/bin/python', cwd='/workspace', args=[
        SERVER, '--allocation-directory', '/evidence/allocation', '--app', 'inkscape',
        '--seed', '991120', '--max-stages', '2', '--harness-python', '/usr/bin/python3'],
        env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1',
             'PYTHONPATH': '/workspace:/workspace/research/live_control',
             'HOME': '/tmp/host-image-home'})
    Path('/tmp/host-image-home').mkdir(exist_ok=True)
    with (ROOT/'mcp-stderr.log').open('w') as errlog:
        async with stdio_client(params, errlog=errlog) as (reader, writer):
            async with ClientSession(reader, writer) as client:
                await client.initialize()
                listed = await client.list_tools()
                names = sorted(tool.name for tool in listed.tools)
                tools_path.write_text(json.dumps(names)+'\n')
                start_entry = time.monotonic_ns()
                start = await client.call_tool('native_start', {'timeout': 30})
                start_return = time.monotonic_ns()
                payload, images = save_response('start.json', start)
                if start.isError or len(images) != 1:
                    (ROOT/'client-result.json').write_text(json.dumps({
                        'status': 'STOP_START_OR_IMAGE_UNAVAILABLE', 'tools': names,
                        'start_entry_ns': start_entry, 'start_return_ns': start_return,
                        'image_count': len(images)}, indent=2)+'\n')
                    return
                (ROOT/'start-boundary.json').write_text(json.dumps({
                    'sdk_entry_ns': start_entry, 'sdk_return_ns': start_return,
                    'content_count': len(start.content), 'image_blocks': images,
                    'image_sha256': hashlib.sha256(Path(images[0]['path']).read_bytes()).hexdigest(),
                    'image_forwarding': 'raw MCP image block bytes saved without transform'},
                    indent=2, sort_keys=True)+'\n')
                meta = json.loads(start.content[0].text)
                context = meta.get('session_context', {})
                source_sequence = meta.get('receipt', {}).get('native_result', {}).get('sequence')
                if type(source_sequence) is not int or source_sequence < 1:
                    source = json.loads((ROOT/'allocation/run/source-1.json').read_text())
                    source_sequence = source['sequence']
                print(json.dumps({'event': 'READY_FOR_MODEL_DECISION',
                    'tool_names': names, 'public_goal': context.get('goal'),
                    'exchange_contract': context.get('exchange_contract'),
                    'source_sequence': source_sequence,
                    'image_path': images[0]['path'], 'image_sha256': __import__('hashlib').sha256(
                        Path(images[0]['path']).read_bytes()).hexdigest()}, sort_keys=True), flush=True)
                line = await asyncio.to_thread(sys.stdin.readline)
                if not line:
                    (ROOT/'client-result.json').write_text(json.dumps({
                        'status': 'STOP_MODEL_DECISION_NOT_RECEIVED', 'tools': names}, indent=2)+'\n')
                    return
                decision = json.loads(line)
                (ROOT/'decision.json').write_text(json.dumps(decision, indent=2, sort_keys=True)+'\n')
                submit_entry = time.monotonic_ns()
                submit = await client.call_tool('native_submit', {
                    'stage': 1, 'decision': decision, 'timeout': 30})
                submit_return = time.monotonic_ns()
                submit_payload, submit_images = save_response('submit.json', submit)
                response_meta = json.loads(submit.content[0].text) if submit.content else {}
                resumed = 0
                while response_meta.get('status') == 'pending' and resumed < 10:
                    digest = response_meta.get('decision_sha256')
                    if not isinstance(digest, str):
                        break
                    resume_entry = time.monotonic_ns()
                    resumed_result = await client.call_tool('native_resume', {
                        'stage': 1, 'decision_sha256': digest, 'timeout': 5})
                    resume_return = time.monotonic_ns()
                    save_response(f'resume-{resumed}.json', resumed_result)
                    response_meta = json.loads(resumed_result.content[0].text) if resumed_result.content else {}
                    with (ROOT/'resume-timings.jsonl').open('a') as stream:
                        stream.write(json.dumps({'entry_ns': resume_entry,
                            'return_ns': resume_return, 'index': resumed})+'\n')
                    resumed += 1
                status_entry = time.monotonic_ns()
                status = await client.call_tool('native_status', {})
                status_return = time.monotonic_ns()
                status_payload, _ = save_response('status.json', status)
                (ROOT/'client-result.json').write_text(json.dumps({
                    'status': 'returned', 'tool_names': names,
                    'submit_is_error': submit.isError, 'submit_metadata': response_meta,
                    'submit_image_blocks': submit_images, 'same_request_resume_count': resumed,
                    'sdk': {'submit_entry_ns': submit_entry, 'submit_return_ns': submit_return,
                            'status_entry_ns': status_entry, 'status_return_ns': status_return},
                    'terminal': json.loads(status.content[0].text).get('allocation')
                        if status.content else None}, indent=2, sort_keys=True)+'\n')
                print(json.dumps({'event': 'FORMAL_COMPLETE',
                    'submit_is_error': submit.isError,
                    'submit_image_count': len(submit_images), 'resume_count': resumed,
                    'status': response_meta.get('status'),
                    'terminal_status': (json.loads(status.content[0].text).get('allocation') or {}).get('status')
                        if status.content else None}, sort_keys=True), flush=True)


asyncio.run(main())
