import asyncio,json,os,sys,time
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    out=Path('results-local/native-mcp-managed-01').resolve()
    out.mkdir(exist_ok=False)
    params=StdioServerParameters(command=sys.executable,args=[
        str(Path('research/live_control/native_mcp_v1.py').resolve()),
        '--allocation-directory',str(out/'allocation'),'--app','inkscape',
        '--seed','991117','--max-stages','2','--harness-python','/usr/bin/python3'],env=dict(os.environ))
    with (out/'mcp-stderr.log').open('w') as log:
        async with stdio_client(params,errlog=log) as (r,w):
            async with ClientSession(r,w) as client:
                await client.initialize()
                (out/'tools.json').write_text((await client.list_tools()).model_dump_json())
                start_index=0
                deadline=time.monotonic()+60
                while True:
                    result=await client.call_tool('native_start',{'timeout':0 if start_index==0 else 5})
                    (out/f'start-{start_index}.json').write_text(result.model_dump_json())
                    metadata=json.loads(result.content[0].text)
                    start_index+=1
                    if metadata.get('allocation',{}).get('status')!='starting':break
                    if time.monotonic()>deadline:raise TimeoutError('same allocation still starting; inspect, do not restart')
                print(result.model_dump_json(),flush=True)
                if metadata.get('allocation',{}).get('status')!='ready':return
                deadline=time.monotonic()+240
                path=out/'decision.json'
                while not path.exists():
                    if time.monotonic()>deadline:raise TimeoutError('no primary decision; harness owns its existing deadline')
                    await asyncio.sleep(.05)
                decision=json.loads(path.read_bytes())
                result=await client.call_tool('native_submit',{'stage':1,'decision':decision})
                (out/'submit.json').write_text(result.model_dump_json())
                print(result.model_dump_json(),flush=True)
                statuses=[]
                for _ in range(20):
                    status=await client.call_tool('native_status',{})
                    row=json.loads(status.content[0].text);statuses.append(row)
                    if row.get('allocation',{}).get('status')=='terminal':break
                    await asyncio.sleep(.1)
                (out/'statuses.json').write_text(json.dumps(statuses,indent=2)+'\n')
                print(json.dumps({'owner_status':statuses[-1]}),flush=True)

asyncio.run(main())
