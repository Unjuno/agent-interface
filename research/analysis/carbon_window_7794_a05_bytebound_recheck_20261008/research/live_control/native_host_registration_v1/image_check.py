"""Windows SDK -> WSL stdio image read, without starting or submitting input."""
import asyncio,base64,hashlib,json,os
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
repo=Path(__file__).resolve().parents[3]
run=repo/'results-local/native-multiapp-integration-01/run'
args=['-d','Ubuntu','--cd','/mnt/c/Users/junny/Documents/New project/agent-interface-admission-audit',
      '--exec','env','PYTHONDONTWRITEBYTECODE=1','PYTHONPATH=.:research/live_control',
      '/tmp/agent-interface-mcp-venv/bin/python','research/live_control/native_mcp_v1.py',
      '--run-directory','results-local/native-multiapp-integration-01/run']
def snapshot():
    return {str(p.relative_to(run)): [hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns]
            for p in run.rglob('*') if p.is_file()}
async def main():
    before=snapshot()
    async with stdio_client(StdioServerParameters(command='wsl.exe',args=args,env=dict(os.environ))) as (reader,writer):
        async with ClientSession(reader,writer) as client:
            await client.initialize()
            result=await client.call_tool('native_observe',{'stage':7})
            assert not result.isError
            meta=json.loads(result.content[0].text)
            blocks=[b for b in result.content if b.type=='image'];assert len(blocks)==1
            image=base64.b64decode(blocks[0].data,validate=True)
            ref=meta['image_reference'];expected=(run/ref['relative_path']).read_bytes()
            assert image==expected and hashlib.sha256(image).hexdigest()==ref['sha256']
    assert snapshot()==before
    report={'scope':'Windows SDK receives retained WSL image; not direct model-host tool use',
        'source_commit':'36bdf3404','tool':'native_observe','stage':7,
        'image_bytes':len(image),'image_sha256':ref['sha256'],'image_sequence':ref['sequence'],
        'mime_type':blocks[0].mimeType,'files_unchanged':len(before),
        'command':'wsl.exe','arguments':args,'model_callable_tools_present':False,
        'gui_started':False,'input_submitted':False}
    with (Path(__file__).parent/'image-check.json').open('x',encoding='utf-8') as output:
        json.dump(report,output,indent=2)
    print(json.dumps(report,ensure_ascii=True))
asyncio.run(main())
