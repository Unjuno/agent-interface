import asyncio,json,os
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
async def main():
    args=['-d','Ubuntu','--cd','/mnt/c/Users/junny/Documents/New project/agent-interface-admission-audit','--exec','env','PYTHONDONTWRITEBYTECODE=1','PYTHONPATH=.:research/live_control','/tmp/agent-interface-mcp-venv/bin/python','research/live_control/native_mcp_v1.py','--allocation-directory','results-local/native-host-direct-01','--app','calc','--seed','991125','--max-stages','8','--text-gap-ms','2','--harness-python','/usr/bin/python3']
    async with stdio_client(StdioServerParameters(command='wsl.exe',args=args,env=dict(os.environ))) as (reader,writer):
        async with ClientSession(reader,writer) as client:
            await client.initialize()
            listed=await client.list_tools()
            status=await client.call_tool('native_status',{})
            report={'command':'wsl.exe','args':args,'tools':[t.name for t in listed.tools],'status':json.loads(status.content[0].text),'allocation_exists':Path('results-local/native-host-direct-01').exists()}
            assert report['status']['allocation']['status']=='not_started'
            assert not report['allocation_exists']
            Path('results-local/native-host-handshake.json').write_text(json.dumps(report,indent=2))
            print(json.dumps({'tools':report['tools'],'status':'not_started','allocation_exists':False}))
asyncio.run(main())
