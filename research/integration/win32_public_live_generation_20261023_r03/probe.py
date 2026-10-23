"""One-shot live HWND-generation check through the guarded Win32 MCP route."""
from __future__ import annotations
import asyncio
import datetime as dt
import json
import os
from pathlib import Path
import argparse
import subprocess
import sys
import tempfile
import time
import traceback

PACKET=Path(__file__).resolve().parent
ROOT=PACKET.parents[2]
sys.path.insert(0,str(ROOT))
CONDITIONS=json.loads((PACKET/'conditions.json').read_text(encoding='utf-8'))
RAW=PACKET/'raw.json'
if sys.platform!='win32': raise SystemExit('requires native Windows')


def start_fixture(label,folder):
    folder.mkdir(parents=True)
    meta,effect,events=(folder/n for n in ('fixture-meta.json','effect.json','events.jsonl'))
    log=(folder/'fixture.log').open('wb')
    p=subprocess.Popen([sys.executable,'-m','runtime.backends.win32_v1.fixture_app',
        '--meta',str(meta),'--effect',str(effect),'--events',str(events)],
        cwd=str(ROOT),stdout=log,stderr=subprocess.STDOUT,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    end=time.monotonic()+8
    while time.monotonic()<end and not meta.exists():
        if p.poll() is not None: raise RuntimeError(f'{label} exited before ready: {p.returncode}')
        time.sleep(.02)
    if not meta.exists():
        p.terminate(); p.wait(timeout=2); raise TimeoutError(f'{label} fixture not ready')
    return {'label':label,'pid':p.pid,'hwnd':int(json.loads(meta.read_text(encoding='utf-8'))['hwnd']),
            'meta_path':str(meta),'effect_path':str(effect),'events_path':str(events),
            'log_path':str(folder/'fixture.log'),'process':p,'log':log,'started_utc':dt.datetime.now(dt.timezone.utc).isoformat()}


def close_fixture(row):
    if row is None: return
    from ctypes import wintypes
    import ctypes
    u=ctypes.WinDLL('user32',use_last_error=True)
    u.PostMessageW.argtypes=(wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM)
    u.PostMessageW.restype=wintypes.BOOL
    u.IsWindow.argtypes=(wintypes.HWND,); u.IsWindow.restype=wintypes.BOOL
    row['close_posted']=bool(u.PostMessageW(row['hwnd'],0x0010,0,0))
    try: row['exit_code']=row['process'].wait(timeout=5)
    except subprocess.TimeoutExpired:
        row['terminate_attempted']=True; row['process'].terminate()
        try: row['exit_code']=row['process'].wait(timeout=2)
        except subprocess.TimeoutExpired:
            row['kill_attempted']=True; row['process'].kill(); row['exit_code']=row['process'].wait(timeout=2)
    row['window_exists_after_exit']=bool(u.IsWindow(row['hwnd']))
    row['log'].close(); row.pop('process',None); row.pop('log',None)


class NoopSupervisor:
    def __init__(self,owner): self.owner=owner
    def producer_started(self,*args,**kwargs): return self.owner.producer_started(*args,**kwargs)
    def cancel(self,operation_id,target_generation,*,cleanup_deadline_ns):
        return self.owner.request_cancel(operation_id,target_generation,cleanup_deadline_ns=cleanup_deadline_ns)
    def close(self): return None


def _json(result):
    return {'is_error':bool(result.isError),
            'data':json.loads(result.content[0].text) if result.content else None}


def run():
    if RAW.exists() or (PACKET/'run').exists(): raise SystemExit('R02 output exists; refusing overwrite')
    out=PACKET/'run'; out.mkdir()
    record={'schema':'win32-public-live-generation-raw-v1','attempt_id':CONDITIONS['attempt_id'],
        'source_commit':CONDITIONS['source_commit'],'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'platform':sys.platform,'resource_commands':[],'scope':CONDITIONS['scope'],
        'producer_factory_calls':[],'status':'FAIL_OR_UNKNOWN','fixtures':[]}
    try:
        from runtime.backends.win32_v1.backend import Win32Backend
        from runtime.cli_v1.mcp_server import create_server
        from runtime.cli_v1.owned_win32_session import OwnedWin32SessionOwner
        from runtime.guarded_win32_v1.operation_owner import OperationOwner
        active={'hwnd':None}
        backend_holder=[]; owner_holder=[]
        a=start_fixture('generation-a',out/'generation-a'); record['fixtures'].append(a)
        active['hwnd']=a['hwnd']
        def reader():
            backend=Win32Backend({'fixture':active['hwnd']}); backend_holder.append(backend)
            return backend.target_generation('fixture')
        generation_a=reader(); record['generation_a']=generation_a
        def make_owner(_targets,_root,_display):
            op=OperationOwner(clock_ns=time.monotonic_ns,process_identity_reader=lambda _p:None)
            adapter=OwnedWin32SessionOwner(op,NoopSupervisor(op))
            adapter.bind_target_generation_reader(reader); owner_holder.append((adapter,op))
            return adapter
        def forbidden_producer(action):
            record['producer_factory_calls'].append(action.get('operation_id'))
            raise AssertionError('producer factory must not run after generation mismatch')
        with tempfile.TemporaryDirectory() as mcp_root:
            server=create_server({'fixture':a['hwnd']},mcp_root,session_mode='guarded-win32',
                _guarded_win32_owner_factory=make_owner,
                _guarded_win32_producer_factory=forbidden_producer)
            bound=_json(asyncio.run(server.call_tool('interface_guarded_win32_bind_target',{})))
            record['bind']=bound
            binding=bound['data']
            admitted=_json(asyncio.run(server.call_tool('interface_guarded_win32_admit',{
                'action_operation_id':'c'*32,'target_binding_id':binding['target_binding_id'],
                'operation_deadline_ns':time.monotonic_ns()+10_000_000_000,
                'obligations':['key:CTRL']})))
            record['admit']=admitted
            b=start_fixture('generation-b',out/'generation-b'); record['fixtures'].append(b)
            active['hwnd']=b['hwnd']
            record['generation_b']=reader()
            started=_json(asyncio.run(server.call_tool('interface_guarded_win32_start',{
                'call_id':admitted['data']['call_id'],'wait_for_result_ms':1000})))
            record['start']=started
            retained=_json(asyncio.run(server.call_tool('interface_results',{
                'call_id':admitted['data']['call_id']})))
            record['interface_results']=retained
            adapter,op=owner_holder[0]
            record['owner_result']=op.result('c'*32)
            record['owner_close']=adapter.close()
            d=started.get('data') or {}; action=(retained.get('data') or {}).get('action') or {}
            record['status']='PASS' if (
                not bound['is_error'] and binding.get('target_generation')==generation_a
                and not admitted['is_error'] and (admitted['data'].get('action') or {}).get('target_generation')==generation_a
                and record['generation_b']!=generation_a
                and d.get('status')=='unknown'
                and (action.get('result') or {}).get('error')=='target_generation_changed_before_start'
                and record['producer_factory_calls']==[]
                and d.get('input_dispatched') is False
                and d.get('task_success') is None and d.get('replay_allowed') is False
                and record['owner_result'].get('phase')=='unknown'
                and record['owner_result'].get('replay_allowed') is False) else 'FAIL_OR_UNKNOWN'
    except BaseException as error:
        record['error']={'type':type(error).__name__,'detail':str(error)}
        record['traceback']=traceback.format_exc()
    finally:
        for f in reversed(record['fixtures']):
            try: close_fixture(f)
            except BaseException as error: record.setdefault('cleanup_errors',[]).append({'pid':f.get('pid'),'error':repr(error)})
        for f in record['fixtures']:
            f.pop('started_utc',None)
        record.setdefault('cleanup_errors',[])
        record['ended_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
        RAW.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return 0 if record['status']=='PASS' and not record['cleanup_errors'] else 1

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    if os.environ.get("SOURCE_COMMIT") != CONDITIONS["source_commit"]:
        parser.error("SOURCE_COMMIT does not match frozen conditions")
    return run()

if __name__=='__main__': raise SystemExit(main())
