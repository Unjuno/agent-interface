"""Owned Windows job/process pipe probe; no GUI or native input."""
import ctypes,json,multiprocessing as mp,os,subprocess,sys,threading,time
from ctypes import wintypes
from pathlib import Path

def emit(path,stage,**fields):
    with open(path,"a",encoding="utf-8",newline="\n") as f:
        f.write(json.dumps({"stage":stage,"monotonic_ns":time.monotonic_ns(),**fields},sort_keys=True)+"\n");f.flush();os.fsync(f.fileno())

class BASIC(ctypes.Structure):
    _fields_=[("PerProcessUserTimeLimit",ctypes.c_int64),("PerJobUserTimeLimit",ctypes.c_int64),("LimitFlags",wintypes.DWORD),("MinimumWorkingSetSize",ctypes.c_size_t),("MaximumWorkingSetSize",ctypes.c_size_t),("ActiveProcessLimit",wintypes.DWORD),("Affinity",ctypes.c_size_t),("PriorityClass",wintypes.DWORD),("SchedulingClass",wintypes.DWORD)]
class IO(ctypes.Structure):
    _fields_=[(n,ctypes.c_uint64) for n in ("ReadOperationCount","WriteOperationCount","OtherOperationCount","ReadTransferCount","WriteTransferCount","OtherTransferCount")]
class EXTENDED(ctypes.Structure):
    _fields_=[("BasicLimitInformation",BASIC),("IoInfo",IO),("ProcessMemoryLimit",ctypes.c_size_t),("JobMemoryLimit",ctypes.c_size_t),("PeakProcessMemoryUsed",ctypes.c_size_t),("PeakJobMemoryUsed",ctypes.c_size_t)]

def peer(reader,ready):
    ready.set();time.sleep(10);reader.close()

def worker(root):
    import _winapi
    trace=root/"worker_trace.jsonl";emit(trace,"worker_started",pid=os.getpid())
    if sys.stdin.buffer.read(1)!=b"g":emit(trace,"custody_gate_denied");return 4
    emit(trace,"custody_gate_open")
    ctx=mp.get_context("spawn");reader,writer=ctx.Pipe(duplex=False);ready=ctx.Event()
    proc=ctx.Process(target=peer,args=(reader,ready));proc.start();emit(trace,"peer_started",pid=proc.pid)
    reader.close();emit(trace,"parent_reader_closed")
    try:
        if not ready.wait(2):emit(trace,"peer_not_ready");return 5
        emit(trace,"peer_ready")
        start=time.monotonic_ns()
        ov,err=_winapi.WriteFile(writer.fileno(),b"x"*(8*1024*1024),overlapped=True)
        emit(trace,"write_started",error=err,start_ns=start)
        if err!=_winapi.ERROR_IO_PENDING:emit(trace,"write_not_pending",error=err);return 6
        state=_winapi.WaitForMultipleObjects([ov.event],False,200)
        emit(trace,"deadline_wait",wait_result=state)
        if state!=_winapi.WAIT_TIMEOUT:emit(trace,"unexpected_completion",wait_result=state);return 7
        ov.cancel();emit(trace,"cancel_called")
        cancel_state=_winapi.WaitForMultipleObjects([ov.event],False,500)
        emit(trace,"cancel_completion_wait",wait_result=cancel_state)
        if cancel_state!=_winapi.WAIT_OBJECT_0:emit(trace,"cancel_not_confirmed");return 8
        try:
            count,error=ov.GetOverlappedResult(False);emit(trace,"write_result",bytes=count,error=error)
        except OSError as e:
            count=None;error=getattr(e,"winerror",None);emit(trace,"write_result_exception",error=error,kind=type(e).__name__)
        proc.terminate();proc.join(2);emit(trace,"peer_retired",exited=not proc.is_alive(),exit_code=proc.exitcode)
        writer.close();emit(trace,"writer_closed")
        return 0 if not proc.is_alive() and error==_winapi.ERROR_OPERATION_ABORTED else 9
    finally:
        if proc.is_alive():proc.terminate();proc.join(2)
        emit(trace,"worker_final",peer_exited=not proc.is_alive())

def main(root):
    root.mkdir(parents=True,exist_ok=False);trace=root/"supervisor_trace.jsonl"
    k=ctypes.WinDLL("kernel32",use_last_error=True)
    k.CreateJobObjectW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR];k.CreateJobObjectW.restype=wintypes.HANDLE
    k.SetInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD];k.SetInformationJobObject.restype=wintypes.BOOL
    k.AssignProcessToJobObject.argtypes=[wintypes.HANDLE,wintypes.HANDLE];k.AssignProcessToJobObject.restype=wintypes.BOOL
    k.TerminateJobObject.argtypes=[wintypes.HANDLE,wintypes.UINT];k.TerminateJobObject.restype=wintypes.BOOL
    k.CloseHandle.argtypes=[wintypes.HANDLE];k.CloseHandle.restype=wintypes.BOOL
    job=k.CreateJobObjectW(None,None)
    if not job:raise OSError(ctypes.get_last_error(),"CreateJobObjectW")
    info=EXTENDED();info.BasicLimitInformation.LimitFlags=0x2000
    if not k.SetInformationJobObject(job,9,ctypes.byref(info),ctypes.sizeof(info)):
        code=ctypes.get_last_error();k.CloseHandle(job);raise OSError(code,"SetInformationJobObject")
    child=None;code=None;timed_out=False;assigned=False
    try:
        with open(root/"stdout.bin","xb") as out,open(root/"stderr.bin","xb") as err:
            child=subprocess.Popen([sys.executable,"-B",__file__,"worker",str(root)],stdin=subprocess.PIPE,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
            emit(trace,"worker_started",pid=child.pid)
            assigned=bool(k.AssignProcessToJobObject(job,wintypes.HANDLE(child._handle)))
            emit(trace,"job_assignment",assigned=assigned,error=0 if assigned else ctypes.get_last_error())
            if not assigned:
                child.kill();code=child.wait(timeout=3)
            else:
                child.stdin.write(b"g");child.stdin.flush();child.stdin.close()
                try:code=child.wait(timeout=6)
                except subprocess.TimeoutExpired:
                    timed_out=True;emit(trace,"deadline_expired");k.TerminateJobObject(job,1)
                    try:code=child.wait(timeout=3)
                    except subprocess.TimeoutExpired:code=None
            emit(trace,"worker_wait_complete",exit_code=code,timed_out=timed_out)
    finally:
        if child is not None and child.poll() is None:
            if assigned:k.TerminateJobObject(job,1)
            else:child.kill()
            try:child.wait(timeout=3)
            except subprocess.TimeoutExpired:pass
        k.CloseHandle(job)
    result={"schema":"win32-overlapped-cancel-r07-v1","worker_pid":child.pid if child else None,"exit_code":code,"timed_out":timed_out,"job_assigned":assigned,"worker_exited":child is not None and child.poll() is not None,"scope":"owned Windows job and subprocesses; no GUI or input"}
    (root/"RESULT.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(result,sort_keys=True));return 0 if result["worker_exited"] else 2

if __name__=="__main__":
    if len(sys.argv)==3 and sys.argv[1]=="worker":raise SystemExit(worker(Path(sys.argv[2])))
    if len(sys.argv)==2:raise SystemExit(main(Path(sys.argv[1])))
    raise SystemExit("expected fresh output directory")
