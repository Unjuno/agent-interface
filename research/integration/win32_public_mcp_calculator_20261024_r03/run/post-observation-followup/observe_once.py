import asyncio,base64,json,sys,hashlib,time
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path(__file__).resolve().parents[5]
OUT=Path(__file__).resolve().parent
RUN=OUT
TARGETS=OUT/"targets.json"
TARGETS.write_text(json.dumps({"calculator":55117672}),encoding="utf-8")
def save(name,value): (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def record(name,reply):
 texts=[]; blocks=[]
 for i,item in enumerate(reply.content):
  if getattr(item,"type",None)=="text": texts.append(item.text); blocks.append({"type":"text","sha256":hashlib.sha256(item.text.encode()).hexdigest()})
  elif getattr(item,"type",None)=="image":
   b=base64.b64decode(item.data); fn=f"{name}-{i}.png";(OUT/fn).write_bytes(b);blocks.append({"type":"image","path":fn,"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)})
 parsed=None
 for t in texts:
  try: parsed=json.loads(t);break
  except Exception: pass
 return {"isError":reply.isError,"parsed":parsed,"raw_text":texts,"blocks":blocks}
async def main():
 params=StdioServerParameters(command=sys.executable,args=["-m","runtime.cli_v1.mcp_server","--targets",str(TARGETS),"--output-directory",str(OUT/"server-receipts"),"--session-mode","supervised-win32"],cwd=str(ROOT))
 async with stdio_client(params) as (reader,writer):
  async with ClientSession(reader,writer) as client:
   await client.initialize()
   started=time.monotonic_ns(); r=await client.call_tool("interface_observe",{"target":"calculator","frame":"screen_physical_px","region":[40,32,336,541]}); finished=time.monotonic_ns()
   o=record("observation",r); save("observation.json",{"started_ns":started,"finished_ns":finished,**o})
   c=await client.call_tool("interface_close",{});save("close.json",record("close",c))
if __name__=="__main__": asyncio.run(main())
