import datetime, hashlib, importlib.util, json, os, pathlib, signal, subprocess, sys, time, traceback
root=pathlib.Path(__file__).resolve().parent
src=root/'codex_app_server_client_v2.py'
sp=importlib.util.spec_from_file_location('client_under_test',src)
mod=importlib.util.module_from_spec(sp); sp.loader.exec_module(mod)

def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def proc_state(pid):
    p=pathlib.Path('/proc')/str(pid)/'stat'
    if not p.exists(): return None
    s=p.read_text()
    tail=s[s.rfind(')')+2:].split()
    return {'state':tail[0], 'ppid':int(tail[1]), 'pgrp':int(tail[2])}
def group_pids(pgid):
    rows=[]
    for x in pathlib.Path('/proc').iterdir():
        if not x.name.isdecimal(): continue
        try:
            st=proc_state(int(x.name))
            if st and st['pgrp']==pgid: rows.append(int(x.name))
        except (FileNotFoundError,PermissionError,ProcessLookupError,ValueError): pass
    return sorted(rows)
def wait_pidfile(path, timeout=3):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if path.exists(): return int(path.read_text(encoding='ascii'))
        time.sleep(.01)
    raise TimeoutError('fixture child did not publish grandchild pid')
def wait_dead(pid, timeout=3):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        st=proc_state(pid)
        if st is None or st['state']=='Z': return st
        time.sleep(.02)
    return proc_state(pid)
def run_arm(name, group_mode):
    pidfile=root/(name+'.pid')
    try: pidfile.unlink()
    except FileNotFoundError: pass
    child=root/'fixture_child.py'
    def factory(*cmd, **kw):
        if group_mode: kw['start_new_session']=True
        proc=subprocess.Popen(*cmd,**kw)
        if group_mode:
            def terminate_group():
                try: os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError: pass
            proc.terminate=terminate_group
        return proc
    begin=utc(); client=mod.CodexAppServerClient([sys.executable,str(child),'--pid-file',str(pidfile)],process_factory=factory)
    direct=client.process.pid; grand=wait_pidfile(pidfile); pgid=os.getpgid(direct)
    before={'direct':proc_state(direct),'grandchild':proc_state(grand),'group_pids':group_pids(pgid)}
    error=None; close_start=time.monotonic()
    try: client.close(timeout=.20)
    except BaseException as e: error=type(e).__name__+': '+str(e)
    close_elapsed=time.monotonic()-close_start
    after_close={'direct_rc':client.process.poll(),'direct':proc_state(direct),'grandchild':proc_state(grand),'group_pids':group_pids(pgid),'reader_alive':client._reader.is_alive()}
    cleanup_signal=None
    if proc_state(grand) is not None and proc_state(grand)['state']!='Z':
        try: os.kill(grand,signal.SIGTERM); cleanup_signal='SIGTERM_SENT'
        except ProcessLookupError: cleanup_signal='ALREADY_GONE'
    if client.process.poll() is None:
        try: client.process.kill(); client.process.wait(timeout=2)
        except BaseException: pass
    client._reader.join(timeout=3)
    for f in (client.process.stdin,client.process.stdout,client.process.stderr):
        try: f.close()
        except BaseException: pass
    final={'arm':name,'group_mode':group_mode,'started_utc':begin,'ended_utc':utc(),'direct_pid':direct,'grandchild_pid':grand,'pgid':pgid,'before':before,'close_error':error,'close_elapsed_seconds':close_elapsed,'after_close':after_close,'cleanup_signal':cleanup_signal,'final_direct_rc':client.process.poll(),'final_grandchild':proc_state(grand),'final_reader_alive':client._reader.is_alive()}
    return final
rows=[]
try:
    rows.append(run_arm('direct-child-termination',False))
    rows.append(run_arm('isolated-process-group-termination',True))
except BaseException:
    (root/'runner.exception.txt').write_text(traceback.format_exc(),encoding='utf-8')
    raise
result={'schema':'appserver-descendant-group-a01-v1','source_path':'research/live_control/codex_app_server_client_v2.py','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'main_sha':'4d42238694c55aaa29bf47cb13a5b8d4c5d4074a','python':sys.version,'platform':sys.platform,'arms':rows}
(root/'RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,sort_keys=True))
