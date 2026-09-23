import asyncio, json, os, sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    request=json.load(sys.stdin)
    output=Path(request['out'])
    if output.exists():raise ValueError('fresh caller output required; do not replay')
    output.mkdir(parents=True)
    (output/'request.json').write_text(json.dumps(request,indent=2)+'\n')
    params=StdioServerParameters(command=sys.executable,args=[
        str(Path('research/live_control/native_mcp_v1.py').resolve()),
        '--run-directory',str(Path(request['run_directory']).resolve())],env=dict(os.environ))
    with (output/'server-stderr.txt').open('w') as log:
        async with stdio_client(params,errlog=log) as (reader,writer):
            async with ClientSession(reader,writer) as client:
                init=await client.initialize()
                (output/'initialize.json').write_text(init.model_dump_json())
                tools=await client.list_tools()
                (output/'tools.json').write_text(tools.model_dump_json())
                result=await client.call_tool(request['tool'],request['arguments'])
                encoded=result.model_dump_json()
                (output/'result.json').write_text(encoded)
                print(encoded,flush=True)

asyncio.run(main())
