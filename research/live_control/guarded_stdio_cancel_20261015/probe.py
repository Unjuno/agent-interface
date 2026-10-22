"""Finite actual stdio client/server composition; all X transport is fake."""
import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MATRIX = [(arm,condition) for condition in ('healthy','cancel','expiry') for arm in ('coupled','isolated')]


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as output:
        json.dump(value,output,indent=2);output.write('\n')
def sources():
    return {p.relative_to(ROOT).as_posix():sha(p) for p in
        sorted((ROOT/'runtime').rglob('*.py'))+sorted(HERE.glob('*.py'))+[HERE/'PLAN.md']}
def metadata(response):
    if response.isError: raise RuntimeError(str(response))
    return json.loads(response.content[0].text)


async def cell(directory,arm,condition):
    write(directory/'targets.json',dict(app=20))
    flags = ['-B']+(['-O'] if sys.flags.optimize else [])
    argv = flags+['-m','research.live_control.guarded_stdio_cancel_20261015.server',str(directory),arm,condition]
    params = StdioServerParameters(command=sys.executable,args=argv,cwd=str(ROOT))
    brackets = dict(start=time.perf_counter_ns())
    pending = None
    with (directory/'stderr.log').open('x',encoding='utf-8') as stderr:
        async with stdio_client(params,errlog=stderr) as (reader,writer):
            async with ClientSession(reader,writer) as client:
                await client.initialize()
                tools = {tool.name for tool in (await client.list_tools()).tools}
                source = metadata(await client.call_tool('interface_guarded_observe',{}))
                minted = metadata(await client.call_tool('interface_guarded_mint',dict(alias='field',
                    source_sequence=source['source']['sequence'],point=[8,8],region_size=[12,12])))
                brackets['input_sent'] = time.perf_counter_ns()
                pending = asyncio.create_task(client.call_tool('interface_guarded_input',dict(alias='field',
                    offset=minted['offset'],interaction='keyboard',observe_after=False,
                    tail=[dict(op='key_chord',keys=['CTRL','a'])])))
                try:
                    before,ack,wrong = None,None,None
                    if condition!='healthy':
                        async def await_gate():
                            while not (directory/'gate.json').exists():
                                if pending.done(): raise RuntimeError('input returned before gate: '+str(await pending))
                                await asyncio.sleep(.005)
                        await asyncio.wait_for(await_gate(),3)
                        gate = json.loads((directory/'gate.json').read_bytes())
                        listing = metadata(await client.call_tool('interface_results',{}))
                        call_id = next(r['call_id'] for r in listing['calls'] if r['operation']=='guarded_input')
                        brackets['trigger_sent'] = time.perf_counter_ns()
                        if condition=='cancel':
                            wrong = metadata(await client.call_tool('interface_guarded_cancel',dict(call_id='0'*32)))
                            ack = metadata(await client.call_tool('interface_guarded_cancel',dict(call_id=call_id)))
                        else: write(directory/'expire.flag',{})
                        brackets['trigger_returned'] = time.perf_counter_ns()
                        if arm=='isolated':
                            response = await asyncio.wait_for(asyncio.shield(pending),3)
                            brackets['input_result_received'] = time.perf_counter_ns()
                        before = dict(gate=gate,input_result_received=pending.done(),ack=ack,wrong=wrong,
                            state=json.loads((directory/'state.json').read_bytes()),
                            release_flag_exists=(directory/'release.flag').exists(),call_id=call_id)
                        brackets['gate_release'] = time.perf_counter_ns()
                        write(directory/'release.flag',{})
                    if 'input_result_received' not in brackets:
                        response = await asyncio.wait_for(asyncio.shield(pending),3)
                        brackets['input_result_received'] = time.perf_counter_ns()
                    result = metadata(response)
                    state_after = json.loads((directory/'state.json').read_bytes())
                    retained = metadata(await client.call_tool('interface_results',dict(call_id=result['call_id'])))
                    state_lookup = json.loads((directory/'state.json').read_bytes())
                    closed = metadata(await client.call_tool('interface_close',{}))
                    if arm=='isolated':
                        async def await_reader_close():
                            while not (directory/'observation-reader-closed.json').exists(): await asyncio.sleep(.005)
                        await asyncio.wait_for(await_reader_close(),3)
                    row = dict(arm=arm,condition=condition,before_gate_release=before,
                        result=result,retained_result=retained['result'],state_after=state_after,
                        state_after_lookup=state_lookup,close=closed,tools=sorted(tools),
                        parent_perf_counter_ns=brackets,child_command=[sys.executable,*argv])
                finally:
                    if not (directory/'release.flag').exists(): write(directory/'release.flag',{})
                    if pending is not None and not pending.done():
                        try: await asyncio.wait_for(asyncio.shield(pending),3)
                        except Exception: pass
    row['transport_context_closed'] = True
    brackets['transport_closed'] = time.perf_counter_ns()
    return row


async def collect(output):
    output.mkdir()
    rows=[]
    for arm,condition in MATRIX:
        directory=output/(arm+'-'+condition);directory.mkdir()
        row=await cell(directory,arm,condition);write(directory/'cell.json',row);rows.append(row)
    write(output/'raw.json',dict(scope='REAL_STDIO_FAKE_X_CANCELLATION',cases=rows,
        freeze_sha256=sha(HERE/'SOURCE_FREEZE.json'),source_postcheck=sources()==json.loads((HERE/'SOURCE_FREEZE.json').read_bytes())['files'],
        optimized=sys.flags.optimize,python=sys.version,platform=platform.platform(),parent_pid=os.getpid(),live_allocations=0))
    write(output/'FILES.json',{p.relative_to(output).as_posix():sha(p) for p in sorted(output.rglob('*')) if p.is_file()})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');parser.add_argument('--output-dir',type=Path)
    args=parser.parse_args()
    if args.freeze:
        write(HERE/'SOURCE_FREEZE.json',dict(base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            matrix=MATRIX,files=sources(),dependencies={name:importlib.metadata.version(name) for name in ('mcp','python-xlib','Pillow')}))
        return
    if sources()!=json.loads((HERE/'SOURCE_FREEZE.json').read_bytes())['files']: raise RuntimeError('source differs from freeze')
    if args.output_dir is None: parser.error('fresh output directory required')
    asyncio.run(collect(args.output_dir.resolve()))


if __name__=='__main__': main()
