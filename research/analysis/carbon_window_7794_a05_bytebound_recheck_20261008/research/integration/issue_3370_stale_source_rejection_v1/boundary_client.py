"""One-shot MCP stale-source rejection control; never retries an input."""
import asyncio
import base64
import hashlib
import json
from pathlib import Path
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT=Path('/evidence/stale_source')

def persist(name,result):
    payload=result.model_dump(mode='json')
    (ROOT/name).write_text(json.dumps(payload,sort_keys=True)+'\n')
    image_rows=[]
    for i,block in enumerate(result.content):
        if block.type=='image':
            data=base64.b64decode(block.data,validate=True)
            path=ROOT/f'{name.removesuffix(".json")}-image-{i}.png'
            path.write_bytes(data)
            image_rows.append({'path':path.name,'bytes':len(data),
                'sha256':hashlib.sha256(data).hexdigest()})
    return payload,image_rows

def metadata(payload):
    if payload.get('isError'):
        return {'parse':'mcp_error','text':[b.get('text','') for b in payload.get('content',[])]}
    for block in payload.get('content',[]):
        if block.get('type')=='text':
            try:
                return json.loads(block['text'])
            except (ValueError,TypeError):
                return {'parse':'non_json','text':block.get('text','')}
    return {'parse':'no_text'}

async def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    params=StdioServerParameters(command='/opt/mcp/bin/python',cwd='/workspace',args=[
        '/workspace/research/live_control/native_mcp_v1.py','--allocation-directory',
        str(ROOT/'allocation'),'--app','inkscape','--seed','991123','--max-stages','3',
        '--harness-python','/usr/bin/python3'],env={**__import__('os').environ,
        'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':'/workspace:/workspace/research/live_control',
        'HOME':'/tmp/3370-stale-source-home'})
    Path('/tmp/3370-stale-source-home').mkdir(exist_ok=True)
    with (ROOT/'mcp-stderr.log').open('w') as err:
      async with stdio_client(params,errlog=err) as (reader,writer):
       async with ClientSession(reader,writer) as client:
        await client.initialize()
        listed=await client.list_tools()
        (ROOT/'tools.json').write_text(json.dumps(sorted(t.name for t in listed.tools))+'\n')
        start=await client.call_tool('native_start',{'timeout':30})
        start_payload,start_images=persist('start.json',start)
        (ROOT/'start-meta.json').write_text(json.dumps(metadata(start_payload),indent=2,sort_keys=True)+'\n')
        (ROOT/'start-images.json').write_text(json.dumps(start_images,indent=2,sort_keys=True)+'\n')
        if start.isError or len(start_images)!=1:
            (ROOT/'client-result.json').write_text(json.dumps({'disposition':'STOP_START_OR_IMAGE',
                'is_error':start.isError,'images':start_images},indent=2)+'\n')
            return
        observe=await client.call_tool('native_submit',{'stage':1,'decision':{
            'source_sequence':1,'interaction':'observe'},'timeout':10})
        observe_payload,observe_images=persist('observe.json',observe)
        observe_meta=metadata(observe_payload)
        (ROOT/'observe-meta.json').write_text(json.dumps(observe_meta,indent=2,sort_keys=True)+'\n')
        (ROOT/'observe-images.json').write_text(json.dumps(observe_images,indent=2,sort_keys=True)+'\n')
        if observe.isError or observe_meta.get('status')!='boundary':
            (ROOT/'client-result.json').write_text(json.dumps({'disposition':'STOP_OBSERVE_BOUNDARY',
                'is_error':observe.isError,'meta':observe_meta},indent=2)+'\n')
            return
        stale=await client.call_tool('native_submit',{'stage':2,'decision':{
            'source_sequence':1,'point':[600,389],'expected_title':'Inkscape','interaction':'click',
            'tail':[{'op':'key_chord','keys':['Right'],'repeat':18}],
            'finish_after':True},'timeout':2})
        stale_payload,_=persist('stale-submit.json',stale)
        stale_meta=metadata(stale_payload)
        (ROOT/'stale-submit-meta.json').write_text(json.dumps(stale_meta,indent=2,sort_keys=True)+'\n')
        polls=[]
        last=None
        for _ in range(40):
            status=await client.call_tool('native_status',{})
            payload,_=persist('status.json',status)
            last=metadata(payload)
            allocation=last.get('allocation',{}) if isinstance(last,dict) else {}
            polls.append(allocation.get('status'))
            if allocation.get('status') in ('terminal','needs_review'):
                break
            await asyncio.sleep(.1)
        result={'disposition':'CONTROL_CAPTURED','start_is_error':start.isError,
            'start_images':start_images,'observe_is_error':observe.isError,
            'observe_meta':observe_meta,'observe_images':observe_images,
            'stale_is_error':stale.isError,'stale_meta':stale_meta,
            'status_polls':polls,'final_status':last}
        (ROOT/'client-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(json.dumps({'event':'STALE_CONTROL_COMPLETE','stale_is_error':stale.isError,
            'status_polls':polls,'final_status':last},sort_keys=True),flush=True)

asyncio.run(main())
