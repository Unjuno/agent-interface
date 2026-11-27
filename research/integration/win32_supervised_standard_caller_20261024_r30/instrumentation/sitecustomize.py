"""R30 test-only timestamp wrapper for the Win32 cancellation retirement path."""
import json, os, sys, time
from pathlib import Path
REPO_ROOT=os.environ.get("AGENT_INTERFACE_REPO_ROOT")
if REPO_ROOT and REPO_ROOT not in sys.path: sys.path.insert(0,REPO_ROOT)
TRACE=os.environ.get("AGENT_INTERFACE_CANCEL_TRACE")
def emit(event, **fields):
 if not TRACE: return
 row={"event":event,"pid":os.getpid(),"monotonic_ns":time.perf_counter_ns(),**fields}
 fd=os.open(TRACE,os.O_CREAT|os.O_APPEND|os.O_WRONLY,0o600)
 try: os.write(fd,(json.dumps(row,sort_keys=True)+"\n").encode("utf-8"))
 finally: os.close(fd)
emit("sitecustomize_loaded")
try:
 from runtime.guarded_win32_v1.process_cancellation import OperationCancellationSupervisor
 _original=OperationCancellationSupervisor._retire_process
 def _traced_retire(self, process, deadline_ns):
  pid=getattr(process,"pid",None); name=getattr(process,"name",None)
  emit("retire_enter",target_pid=pid,target_name=name,deadline_ns=deadline_ns)
  saved={}
  for method_name in ("is_alive","terminate","join","kill"):
   try: original=getattr(process,method_name)
   except BaseException: continue
   saved[method_name]=original
   def wrapper(*args,_n=method_name,_f=original,**kwargs):
    emit("process_method_enter",target_pid=pid,target_name=name,method=_n,args_repr=repr(args),kwargs_repr=repr(kwargs))
    start=time.perf_counter_ns()
    try: value=_f(*args,**kwargs)
    except BaseException as error:
     emit("process_method_exception",target_pid=pid,method=_n,elapsed_ns=time.perf_counter_ns()-start,error_type=type(error).__name__,error=str(error)); raise
    emit("process_method_return",target_pid=pid,method=_n,elapsed_ns=time.perf_counter_ns()-start,result_repr=repr(value))
    return value
   setattr(process,method_name,wrapper)
  try:
   result=_original(self,process,deadline_ns)
   emit("retire_return",target_pid=pid,target_name=name,result=result)
   return result
  except BaseException as error:
   emit("retire_exception",target_pid=pid,target_name=name,error_type=type(error).__name__,error=str(error)); raise
  finally:
   for method_name in saved:
    try: delattr(process,method_name)
    except BaseException: setattr(process,method_name,saved[method_name])
 OperationCancellationSupervisor._retire_process=_traced_retire
 emit("retirement_wrapper_installed")
except BaseException as error:
 emit("instrumentation_import_error",error_type=type(error).__name__,error=str(error))
