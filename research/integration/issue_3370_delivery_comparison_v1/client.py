"""One persistent stdio client for one frozen Issue #3370 pair condition."""
import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path('/evidence') / os.environ['DELIVERY_CONDITION']
SEED = int(os.environ.get('ISSUE3370_SEED', '991123'))
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
            images.append({'index': index, 'path': str(path), 'bytes': len(data),
                           'sha256': hashlib.sha256(data).hexdigest()})
    return payload, images


async def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    params = StdioServerParameters(command='/opt/mcp/bin/python', cwd='/workspace', args=[
        SERVER, '--allocation-directory', str(ROOT/'allocation'), '--app', 'inkscape',
        '--seed', str(SEED), '--max-stages', '2', '--harness-python', '/usr/bin/python3'],
        env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1',
             'PYTHONPATH': '/workspace:/workspace/research/live_control',
             'HOME': '/tmp/3370-delivery-home'})
    Path('/tmp/3370-delivery-home').mkdir(exist_ok=True)
    with (ROOT/'mcp-stderr.log').open('w') as errlog:
        async with stdio_client(params, errlog=errlog) as (reader, writer):
            async with ClientSession(reader, writer) as client:
                await client.initialize()
                names = sorted(tool.name for tool in (await client.list_tools()).tools)
                (ROOT/'tools.json').write_text(json.dumps(names)+'\n')
                entry = time.monotonic_ns()
                start = await client.call_tool('native_start', {'timeout': 30})
                returned = time.monotonic_ns()
                _, images = save_response('start.json', start)
                if start.isError or len(images) != 1:
                    (ROOT/'client-result.json').write_text(json.dumps({
                        'status': 'STOP_START_OR_IMAGE_UNAVAILABLE',
                        'image_count': len(images), 'tools': names}, indent=2)+'\n')
                    return
                meta = json.loads(start.content[0].text)
                sequence = meta.get('receipt', {}).get('native_result', {}).get('sequence')
                if type(sequence) is not int:
                    sequence = json.loads((ROOT/'allocation/run/source-1.json').read_text())['sequence']
                (ROOT/'start-boundary.json').write_text(json.dumps({
                    'sdk_entry_ns': entry, 'sdk_return_ns': returned,
                    'content_count': len(start.content), 'image': images[0],
                    'source_sequence': sequence}, indent=2, sort_keys=True)+'\n')
                print(json.dumps({'event':'READY_FOR_MODEL_DECISION',
                    'condition':os.environ['DELIVERY_CONDITION'], 'seed':SEED,
                    'source_sequence':sequence, 'goal':meta.get('session_context',{}).get('goal'),
                    'image_path':images[0]['path'], 'image_sha256':images[0]['sha256'],
                    'tool_names':names}, sort_keys=True), flush=True)
                decision_path = ROOT/'model-decision.json'
                deadline = time.monotonic()+300
                while not decision_path.exists() and time.monotonic()<deadline:
                    await asyncio.sleep(.1)
                if not decision_path.exists():
                    (ROOT/'client-result.json').write_text(json.dumps({
                        'status':'STOP_MODEL_DECISION_NOT_RECEIVED','tools':names},indent=2)+'\n')
                    return
                decision = json.loads(decision_path.read_text())
                (ROOT/'decision.json').write_text(json.dumps(decision,indent=2,sort_keys=True)+'\n')
                submit_entry = time.monotonic_ns()
                submit = await client.call_tool('native_submit', {
                    'stage':1,'decision':decision,'timeout':30})
                submit_return = time.monotonic_ns()
                _, feedback_images = save_response('submit.json', submit)
                response_meta = json.loads(submit.content[0].text) if submit.content else {}
                resumes = 0
                while response_meta.get('status') == 'pending' and resumes < 10:
                    digest = response_meta.get('decision_sha256')
                    if not isinstance(digest,str):
                        break
                    resumed = await client.call_tool('native_resume', {
                        'stage':1,'decision_sha256':digest,'timeout':5})
                    _, _ = save_response(f'resume-{resumes}.json',resumed)
                    response_meta = json.loads(resumed.content[0].text) if resumed.content else {}
                    resumes += 1
                status_entry = time.monotonic_ns()
                polls=[]
                for _ in range(50):
                    status = await client.call_tool('native_status',{})
                    status_meta = json.loads(status.content[0].text) if status.content else {}
                    polls.append(status_meta.get('allocation',{}).get('status'))
                    if polls[-1] in ('terminal','needs_review'):
                        break
                    await asyncio.sleep(.1)
                status_return = time.monotonic_ns()
                save_response('status.json',status)
                actions = json.loads((ROOT/'allocation/run/actions.json').read_text()) \
                    if (ROOT/'allocation/run/actions.json').exists() else []
                result = {'status':'returned','condition':os.environ['DELIVERY_CONDITION'],
                    'seed':SEED,'tools':names,'submit_is_error':submit.isError,
                    'submit_metadata':response_meta,'feedback_images':feedback_images,
                    'resume_count':resumes,'action_count':len(actions),'status_polls':polls,
                    'sdk':{'submit_entry_ns':submit_entry,'submit_return_ns':submit_return,
                           'status_entry_ns':status_entry,'status_return_ns':status_return},
                    'container_process':(json.loads(status.content[0].text).get('allocation')
                        if status.content else None)}
                (ROOT/'client-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
                print(json.dumps({'event':'CONDITION_COMPLETE','condition':result['condition'],
                    'error':submit.isError,'resumes':resumes,'actions':len(actions),
                    'status':response_meta.get('status'),'polls':polls},sort_keys=True),flush=True)


asyncio.run(main())
