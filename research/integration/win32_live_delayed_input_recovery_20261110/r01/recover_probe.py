import asyncio,json,sys
from pathlib import Path
from datetime import timedelta
from mcp import ClientSession
from mcp.client.stdio import stdio_client,StdioServerParameters
repo=Path(sys.argv[1]); out=Path(sys.argv[2]); rec=json.loads((out/'source-custody-record.json').read_text(encoding='utf-8-sig'))
args=['-m','runtime.cli_v1.mcp_server','--targets',str(out/'targets.json'),'--output-directory',str(out/'mcp-recovery'),'--session-mode','supervised-win32','--supervised-win32-late-input-horizon-ms','2000']
def raw(x): return x.model_dump(mode='json',exclude_none=True)
def texts(x): return [b.text for b in x.content if getattr(b,'type',None)=='text']
async def main():
  params=StdioServerParameters(command=sys.executable,args=args,cwd=str(repo))
  async with stdio_client(params) as (read,write):
    async with ClientSession(read,write,read_timeout_seconds=timedelta(seconds=30)) as s:
      await s.initialize()
      result=await s.call_tool('interface_recover_orphaned_input',{'source_operation_id':rec['operation_id'],'source_target_generation':rec['target_generation'],'obligations':rec['obligations'],'source_custody_record':rec})
      value=raw(result); (out/'recovery-result.json').write_text(json.dumps(value,indent=2),encoding='utf-8')
      print(json.dumps({'isError':result.isError,'text':texts(result)},indent=2))
asyncio.run(main())
