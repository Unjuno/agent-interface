import asyncio, base64, json, os, sys, time
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    out=Path('results-local/native-mcp-timed-01').resolve()
    out.mkdir(exist_ok=False)
    events=[]
    def save(name,value):
        (out/name).write_text(json.dumps(value,indent=2)+'\n')
    async def call(client,name,args,label):
        row={'tool':name,'arguments':args,'sdk_entry_ns':time.monotonic_ns()}
        events.append(row)
        try:
            result=await client.call_tool(name,args)
            row['sdk_return_ns']=time.monotonic_ns()
            row['is_error']=result.isError
        except BaseException as error:
            row.update(sdk_error_ns=time.monotonic_ns(),error=repr(error))
            save('timings.json',events)
            raise
        save('timings.json',events)
        (out/(label+'.json')).write_text(result.model_dump_json())
        for index,block in enumerate(result.content):
            if block.type=='image':
                (out/(label+f'-image-{index}.png')).write_bytes(base64.b64decode(block.data))
        metadata=json.loads(result.content[0].text)
        print(json.dumps({'label':label,'sdk_ms':(row['sdk_return_ns']-row['sdk_entry_ns'])/1e6,
                          'allocation':metadata.get('allocation'),'error':metadata.get('error'),
                          'image_files':[str(p) for p in out.glob(label+'-image-*.png')]}),flush=True)
        return metadata
    params=StdioServerParameters(command=sys.executable,args=[
        str(Path('research/live_control/native_mcp_v1.py').resolve()),
        '--allocation-directory',str(out/'allocation'),'--app','inkscape',
        '--seed','991118','--max-stages','2','--harness-python','/usr/bin/python3'],env=dict(os.environ))
    with (out/'mcp-stderr.log').open('w') as log:
        async with stdio_client(params,errlog=log) as (r,w):
            async with ClientSession(r,w) as client:
                await client.initialize()
                (out/'tools.json').write_text((await client.list_tools()).model_dump_json())
                for i in range(12):
                    meta=await call(client,'native_start',{'timeout':5},f'start-{i}')
                    if meta.get('allocation',{}).get('status')!='starting':break
                if meta.get('allocation',{}).get('status')!='ready':
                    raise RuntimeError('startup not ready; inspect same allocation')
                save('context.json',meta.get('session_context'))
                deadline=time.monotonic()+240
                while not (out/'decision.json').exists():
                    if time.monotonic()>deadline:raise TimeoutError('no primary decision; no restart')
                    await asyncio.sleep(.05)
                decision=json.loads((out/'decision.json').read_bytes())
                meta=await call(client,'native_submit',{'stage':1,'decision':decision},'submit')
                if meta.get('status')=='pending':
                    await call(client,'native_resume',{'stage':1,'decision_sha256':meta['decision_sha256']},'resume')
                for i in range(20):
                    meta=await call(client,'native_status',{},f'status-{i}')
                    if meta.get('allocation',{}).get('status')=='terminal':break
                    await asyncio.sleep(.1)
asyncio.run(main())
