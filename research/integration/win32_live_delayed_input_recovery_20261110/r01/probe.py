import asyncio, json, sys
from datetime import timedelta
from pathlib import Path
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

root = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
args = ['-m','runtime.cli_v1.mcp_server','--targets',str(out/'targets.json'),
        '--output-directory',str(out/'mcp'),'--session-mode','supervised-win32',
        '--supervised-win32-late-input-horizon-ms','2000']
async def main():
    params=StdioServerParameters(command=sys.executable,args=args,cwd=str(root))
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write,read_timeout_seconds=timedelta(seconds=30)) as session:
            init=await session.initialize()
            tools=await session.list_tools()
            obs=await session.call_tool('interface_observe',{
                'target':'fixture','frame':'screen_physical_px','region':[87,80,406,213]})
            def dump(x): return x.model_dump(mode='json',exclude_none=True)
            (out/'mcp-tools.json').write_text(json.dumps(dump(tools),indent=2),encoding='utf-8')
            (out/'observation.json').write_text(json.dumps(dump(obs),indent=2),encoding='utf-8')
            texts=[getattr(b,'text','') for b in obs.content if getattr(b,'type',None)=='text']
            print(json.dumps({'initialize':dump(init),'tools':[t.name for t in tools.tools],
                'observation_text':texts[:1]},indent=2))
asyncio.run(main())


