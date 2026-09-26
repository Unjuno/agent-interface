"""Prepare and verify a fresh host connection without starting its allocation."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

repo = Path(__file__).resolve().parents[2]
out = Path(__file__).resolve().parent
allocation = repo/'results-local/native-host-integration-02'
args = ['-d','Ubuntu','--cd',
        '/mnt/c/Users/junny/Documents/New project/agent-interface-public-review',
        '--exec','env','PYTHONDONTWRITEBYTECODE=1','PYTHONPATH=.:research/live_control',
        '/tmp/agent-interface-mcp-venv/bin/python','research/live_control/native_mcp_v1.py',
        '--allocation-directory','results-local/native-host-integration-02',
        '--app','inkscape','--seed','991284','--max-stages','8','--text-gap-ms','2',
        '--harness-python','/usr/bin/python3']

async def main():
    assert not allocation.exists(), 'fresh allocation required; never remove or relaunch existing evidence'
    config = '[mcp_servers.agent-interface-integration]\ncommand = "wsl.exe"\n'
    config += 'args = '+json.dumps(args)+'\nstartup_timeout_sec = 30\ntool_timeout_sec = 45\n'
    (out/'server-fragment.toml').write_text(config, encoding='utf-8')
    with (out/'server.log').open('w', encoding='utf-8') as log:
        async with stdio_client(StdioServerParameters(command='wsl.exe', args=args, env=dict(os.environ)), errlog=log) as (reader,writer):
            async with ClientSession(reader,writer) as client:
                await client.initialize()
                listed = (await client.list_tools()).model_dump(mode='json')
                (out/'tools.json').write_text(json.dumps(listed,indent=2),encoding='utf-8')
                response = (await client.call_tool('native_status',{})).model_dump(mode='json')
                (out/'status-response.json').write_text(json.dumps(response,indent=2),encoding='utf-8')
                status = json.loads(response['content'][0]['text'])
                assert status['allocation']['status'] == 'not_started', status
                assert status['allocation']['app'] == 'inkscape'
                assert not allocation.exists()
                assert 'Exact complete application window title' in json.dumps(listed)
    revision = subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    report = {'status':'PASS_HANDSHAKE_ONLY','source_revision':revision,
              'command':'wsl.exe','args':args,'allocation_exists':allocation.exists(),
              'gui_started':False,'input_submitted':False,'host_config_modified':False,
              'scope':'Windows SDK to WSL; active host reload and primary live use unverified'}
    (out/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))

asyncio.run(asyncio.wait_for(main(),timeout=45))
