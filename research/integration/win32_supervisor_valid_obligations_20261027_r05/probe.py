"""Owned Windows job/process pipe probe; no GUI or native input."""
import ctypes,importlib.util,json,multiprocessing as mp,os,subprocess,sys,threading,time
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
    trace=root/"worker_trace.jsonl";emit(trace,"worker_started",pid=os.getpid())
    if sys.stdin.buffer.read(1)!=b"g":emit(trace,"custody_gate_denied");return 4
    emit(trace,"custody_gate_open")
    spec=importlib.util.spec_from_file_location("supervisor_source",Path(__file__).with_name("process_cancellation_source.py"))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    ctx=mp.get_context("spawn");reader,writer=ctx.Pipe(duplex=False);ready=ctx.Event()
    proc=ctx.Process(target=peer,args=(reader,ready));proc.start();emit(trace,"peer_started",pid=proc.pid)
    reader.close();emit(trace,"parent_reader_closed")
    supervisor=object.__new__(mod.OperationCancellationSupervisor)
    supervisor._helpers={"recovery":{"process":proc,"connection":writer,"lock":threading.Lock(),"available":True,"identity":"fake-identity"}}
    supervisor._clock_ns=time.monotonic_ns;supervisor._terminate_grace_s=0;supervisor._kill_grace_s=0;supervisor._poll_interval_s=.01
    supervisor._process_identity_reader=lambda _:"fake-identity"
    def load_source(name, filename):
        source_spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(filename))
        source_module=importlib.util.module_from_spec(source_spec);source_spec.loader.exec_module(source_module);return source_module
    contract=load_source("contract_source", "contract_source.py")
    obligations_source=load_source("input_obligations_source", "input_obligations_source.py")
    chars="".join(chr(i) for i in range(0x10000) if not 0xD800<=i<=0xDFFF)
    chunks=[chars[i:i+16384] for i in range(0,len(chars),16384)]
    program={"schema":contract.SCHEMA_PROGRAM,"program_id":"finite-large","source":{"observation_seq":1,"binding_revision":1},"authority":{"lease_id":"finite-large","expires_at_ns":10**18},"terminal":{"release_all_required":True},"ops":[{"op":"focus","target":"fixture"},*[{"op":"text","text":chunk} for chunk in chunks],{"op":"release_all"}]}
    contract.validate_program(program)
    obligations=obligations_source.derive_input_obligations(program)
    from multiprocessing.reduction import ForkingPickler
    entered=threading.Event();finished=threading.Event();outcome=[]
    deadline=time.monotonic_ns()+200_000_000
    request={"operation_id":"a"*32,"target_generation":"b"*64,"recovery_id":"c"*32,"request_id":"c"*32,"deadline_ns":deadline,"obligations":obligations}
    emit(trace,"valid_request_prepared",operation_count=len(program["ops"]),obligation_count=len(obligations),pickle_bytes=len(ForkingPickler.dumps(request)))
    def exchange():
        emit(trace,"exchange_entered",deadline_ns=deadline);entered.set()
        try:supervisor._exchange_helper("recovery",request,deadline);outcome.append("returned")
        except BaseException as e:outcome.append(type(e).__name__)
        finally:emit(trace,"exchange_finished",outcome=outcome,helper_available=supervisor._helpers["recovery"]["available"]);finished.set()
    t=threading.Thread(target=exchange,daemon=True)
    try:
        if not ready.wait(2):emit(trace,"peer_not_ready");return 5
        emit(trace,"peer_ready");t.start()
        if not entered.wait(1):emit(trace,"exchange_not_entered");return 6
        blocked=not finished.wait(.35);emit(trace,"after_cutoff",exchange_blocked=blocked,deadline_ns=deadline)
        proc.terminate();emit(trace,"peer_terminate_requested");proc.join(2)
        exited=not proc.is_alive();emit(trace,"peer_join_returned",exited=exited,exit_code=proc.exitcode)
        done=finished.wait(1);emit(trace,"exchange_observed",finished=done,outcome=outcome)
        if done:writer.close();emit(trace,"writer_closed")
        return 0 if blocked and exited and done and outcome!=["returned"] else 7
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
    result={"schema":"win32-supervisor-valid-obligations-r05-v1","worker_pid":child.pid if child else None,"exit_code":code,"timed_out":timed_out,"job_assigned":assigned,"worker_exited":child is not None and child.poll() is not None,"scope":"owned Windows job and subprocesses; no GUI or input"}
    (root/"RESULT.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(result,sort_keys=True));return 0 if result["worker_exited"] else 2

if __name__=="__main__":
    if len(sys.argv)==3 and sys.argv[1]=="worker":raise SystemExit(worker(Path(sys.argv[2])))
    if len(sys.argv)==2:raise SystemExit(main(Path(sys.argv[1])))
    raise SystemExit("expected fresh output directory")
