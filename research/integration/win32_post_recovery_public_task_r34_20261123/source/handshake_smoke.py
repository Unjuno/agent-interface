from __future__ import annotations
import asyncio, json, sys, time, traceback
from datetime import timedelta
from pathlib import Path
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
ROOT=Path(__file__).resolve().parents[4]
PACKET=ROOT/"research/integration/win32_post_recovery_public_task_r34_20261123"
TARGETS=ROOT/"research/integration/win32_post_recovery_public_task_r31_20261123/raw/trial-01/targets.json"
STATE=ROOT/"research/integration/win32_post_recovery_public_task_r31_20261123/raw/trial-01/fixture-state.json"
EVENTS=ROOT/"research/integration/win32_post_recovery_public_task_r31_20261123/raw/trial-01/events.jsonl"
async def run():
    mode="optimized" if sys.flags.optimize else "normal"
    output=PACKET/"raw"/f"taskserver-handshake-{mode}"
    output.mkdir(parents=True,exist_ok=False)
    args=[]
    if sys.flags.optimize: args.append("-O")
    args += [str(PACKET/"task_oracle_server.py"),str(TARGETS),str(output),str(STATE),str(EVENTS)]
    params=StdioServerParameters(command=sys.executable,args=args,cwd=str(ROOT))
    start=time.monotonic_ns()
    try:
        async with stdio_client(params) as (rd,wr):
            async with ClientSession(rd,wr,read_timeout_seconds=timedelta(seconds=20)) as s:
                await s.initialize()
                listed=await s.list_tools()
                names=sorted(x.name for x in listed.tools)
                assert "interface_verify_task" in names and "interface_dispatch" in names
        result={"mode":mode,"outcome":"PASS_HANDSHAKE_AND_TASK_ORACLE_REGISTERED","tool_count":len(names),"task_oracle_registered":"interface_verify_task" in names,"dispatches":0,"observations":0,"elapsed_ns":time.monotonic_ns()-start}
    except BaseException as exc:
        result={"mode":mode,"outcome":"FAIL_HANDSHAKE","error":repr(exc),"traceback":traceback.format_exc(),"elapsed_ns":time.monotonic_ns()-start}
        (output/"failure.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        raise
    (output/"result.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result))
if __name__=="__main__":
    asyncio.run(run())
