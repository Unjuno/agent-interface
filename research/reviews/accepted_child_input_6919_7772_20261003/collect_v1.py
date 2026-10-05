"""Owned-process collector. Reads exit codes through retained Windows handles, never PID-kills."""
import ctypes, hashlib, json, pathlib, subprocess, sys, time
from ctypes import wintypes
from datetime import datetime, timezone

ROOT=pathlib.Path(__file__).resolve().parent
SOURCE=json.loads((ROOT/'SOURCE.json').read_text())
K=ctypes.WinDLL('kernel32',use_last_error=True)
K.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];K.OpenProcess.restype=wintypes.HANDLE
K.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD];K.WaitForSingleObject.restype=wintypes.DWORD
K.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)];K.GetExitCodeProcess.restype=wintypes.BOOL
K.CloseHandle.argtypes=[wintypes.HANDLE];K.CloseHandle.restype=wintypes.BOOL
def utc():return datetime.now(timezone.utc).isoformat()
def put(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,separators=(',',':'));f.write('\n')
def wait_for(test,limit,label):
    until=time.monotonic()+limit
    while not test():
        if time.monotonic()>until:raise TimeoutError(label)
        time.sleep(.005)
def peer_state(handle):
    wait=K.WaitForSingleObject(handle,0)
    if wait not in (0,258):raise OSError(ctypes.get_last_error(),'WaitForSingleObject')
    code=wintypes.DWORD()
    if not K.GetExitCodeProcess(handle,ctypes.byref(code)):raise OSError(ctypes.get_last_error(),'GetExitCodeProcess')
    return dict(wait=wait,exit_code=code.value)
def run_case(output,case):
    directory=output/case['id'];directory.mkdir()
    phases=[]
    def phase(kind,**fields):phases.append(dict(kind=kind,utc=utc(),**fields))
    argv=[SOURCE['node']['path'],str(ROOT/'owner.mjs'),str(directory),str(ROOT/'source'/case['arm']),
          SOURCE['python']['path'],str(ROOT/'peer.py'),case['mode'],case['boundary']]
    phase('launch',argv=argv)
    handle=None;process=None
    started=time.monotonic()
    with (directory/'stdout.txt').open('xb') as out,(directory/'stderr.txt').open('xb') as err:
        try:
            process=subprocess.Popen(argv,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
            wait_for(lambda:(directory/'peer-started.json').exists(),3,'peer startup')
            peer=json.loads((directory/'peer-started.json').read_text())
            if type(peer['pid']) is not int or peer['parent_pid']!=process.pid or peer['case']!=directory.name:raise ValueError('owned child identity')
            handle=K.OpenProcess(0x00100000|0x1000,False,peer['pid'])
            if not handle:raise OSError(ctypes.get_last_error(),'OpenProcess owned child')
            phase('peer_handle_open',pid=peer['pid'],parent_pid=process.pid,**peer_state(handle))
            (directory/'send-command').touch(exist_ok=False)
            wait_for(lambda:(directory/'accepted.json').exists(),3,'accepted request')
            phase('accepted_before_boundary',primary_exit=process.poll(),**peer_state(handle))
            if (directory/'response-intended.json').exists() or (directory/'synthetic-effect.json').exists():raise ValueError('response barrier bypass')
            (directory/'trigger-boundary').touch(exist_ok=False)
            wait_for(lambda:(directory/'boundary-observed.json').exists() or process.poll() is not None,3,'input boundary')
            phase('boundary_before_permit',observed=(directory/'boundary-observed.json').exists(),primary_exit=process.poll(),
              response_exists=(directory/'response-intended.json').exists(),effect_exists=(directory/'synthetic-effect.json').exists(),**peer_state(handle))
            (directory/'permit-response').touch(exist_ok=False)
            phase('permit_written')
            process.wait(timeout=max(.1,11-(time.monotonic()-started)))
            wait_for(lambda:peer_state(handle)['wait']==0,max(.1,11-(time.monotonic()-started)),'peer actual exit')
            phase('both_processes_terminal',primary_exit=process.returncode,**peer_state(handle))
            receipt=dict(schema='accepted-child-process-receipt-v1',case=case,started_utc=phases[0]['utc'],ended_utc=utc(),
              primary_pid=process.pid,primary_exit=process.returncode,peer_pid=peer['pid'],peer_exit=peer_state(handle)['exit_code'],
              phases=phases,elapsed_seconds=time.monotonic()-started,collector_error=None)
        except Exception as error:
            phase('collector_error',error=repr(error))
            # Only the retained Popen object we created can be stopped on a finite construction failure.
            if process is not None and process.poll() is None:
                process.terminate();process.wait(timeout=3);phase('owned_primary_stopped',primary_exit=process.returncode)
            if handle:
                wait_for(lambda:peer_state(handle)['wait']==0,9,'self-bounded peer terminal after construction failure')
            receipt=dict(schema='accepted-child-process-receipt-v1',case=case,phases=phases,collector_error=repr(error),
              primary_exit=process.returncode if process else None,peer_exit=peer_state(handle)['exit_code'] if handle else None)
            put(directory/'receipt.json',receipt)
            raise
        finally:
            if handle:K.CloseHandle(handle)
    put(directory/'receipt.json',receipt)
    files={str(p.relative_to(directory)).replace('\\','/'):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
           for p in sorted(directory.rglob('*')) if p.is_file()}
    put(directory/'FILES.json',files)
    return receipt

output=(ROOT/sys.argv[1]).resolve()
if ROOT not in output.parents:raise ValueError('output outside owned root')
output.mkdir()
deck=json.loads((ROOT/'DECK.json').read_text()) if len(sys.argv)==2 else [dict(id='smoke-candidate-eof',arm='candidate',mode='success',boundary='eof')]
if len(sys.argv)==2:
    freeze=json.loads((ROOT/'FREEZE.json').read_text())
    for path,expected in freeze['files'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=expected:raise ValueError('frozen source changed '+path)
start=time.monotonic()
with (output/'raw.jsonl').open('x',encoding='utf-8',newline='\n') as raw:
    for case in deck:
        if time.monotonic()-start>89:raise TimeoutError('deck start limit')
        row=run_case(output,case);raw.write(json.dumps(row,separators=(',',':'))+'\n');raw.flush()
        print(json.dumps(dict(case=case['id'],primary=row['primary_exit'],peer=row['peer_exit'])),flush=True)
        if sum(p.stat().st_size for p in output.rglob('*') if p.is_file())>1048576:raise ValueError('output budget')
put(output/'completion.json',dict(rows=len(deck),elapsed_seconds=time.monotonic()-start,utc=utc()))
