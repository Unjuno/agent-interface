import ast
import hashlib
import json
import os
import pathlib
import queue
import subprocess
import sys
import threading
import time
import traceback
from candidate import extract,repair
from cleanup import cleanup

CASES=('healthy','json_fault','ready_then_fault','array','utf8_fault','eof_live')

def is_complete(rows):
    return len(rows)==6 and all(r['child_alive'] is True and not r['fatal'] and not r['cleanup_faults']
        and type(r['cleanup_exit']) is int and r['cleanup_exit']==0 and r['reader_retired'] is True for r in rows)

def measure(wait):
    start=time.monotonic_ns()
    try:
        result=wait(lambda r:r['event']=='ready',timeout=.35)
        end=time.monotonic_ns()
        return dict(outcome=result.get('event','other'),result=result,elapsed_ns=end-start,start_ns=start,end_ns=end,cause=None)
    except Exception as exc:
        cause=exc.__cause__
        end=time.monotonic_ns()
        return dict(outcome=type(exc).__name__,elapsed_ns=end-start,start_ns=start,end_ns=end,
            cause=None if cause is None else dict(type=type(cause).__name__,doc=getattr(cause,'doc',None),
                object_hex=getattr(cause,'object',b'').hex() if isinstance(getattr(cause,'object',None),bytes) else None),
            traceback=traceback.format_exc())

def run(output):
    output.mkdir(parents=True,exist_ok=False)
    root=pathlib.Path(__file__).parent
    original=(root/'source/v39-original.py.txt').read_bytes()
    candidate=(root/'source/v39-candidate.py.txt').read_bytes()
    if repair(original)!=candidate: raise ValueError('candidate inverse closure')
    limits={n:pathlib.Path('/sys/fs/cgroup',n).read_text().strip() for n in ('cpu.max','memory.max','memory.swap.max','pids.max')}
    if os.getuid()!=501 or limits!={'cpu.max':'100000 100000','memory.max':'536870912','memory.swap.max':'0','pids.max':'64'}:
        raise ValueError('runtime allocation')
    runtime=dict(pid=os.getpid(),uid=os.getuid(),limits=limits,python=sys.version,
        cgroup=pathlib.Path('/proc/self/cgroup').read_text(),original_sha256=hashlib.sha256(original).hexdigest(),
        candidate_sha256=hashlib.sha256(candidate).hexdigest())
    (output/'RUNTIME.json').write_text(json.dumps(runtime,sort_keys=True)+'\n')
    factory=extract(candidate)
    rows=[]
    for case in CASES:
        process=None;thread=None;events=[];results=[];fatal=None;unhandled=[];handshake=None
        oldhook=threading.excepthook
        def hook(args): unhandled.append(dict(type=args.exc_type.__name__,traceback=''.join(traceback.format_exception(args.exc_type,args.exc_value,args.exc_traceback))))
        child_alive=False;reader_alive=False
        try:
            process=subprocess.Popen([sys.executable,'-B',str(root/'peer.py'),case,str(output/(case+'-peer.jsonl'))],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='strict',bufsize=1)
            reader,wait,events=factory(process,queue.Queue())
            thread=threading.Thread(target=reader,daemon=True,name='E02-reader-'+case)
            threading.excepthook=hook
            thread.start()
            results.append(measure(wait))
            if case=='ready_then_fault' and results[0]['outcome']=='ready':
                handshake=dict(ready_return_ns=results[0]['end_ns'],continue_start_ns=time.monotonic_ns())
                process.stdin.write('CONTINUE\n');process.stdin.flush()
                handshake['continue_return_ns']=time.monotonic_ns()
                results.append(measure(wait))
            if case not in ('healthy','array'): thread.join(timeout=1)
            child_alive=process.poll() is None
            reader_alive=thread.is_alive()
        except Exception as exc: fatal=dict(error=repr(exc),traceback=traceback.format_exc())
        finally:
            try: exit_code,stderr,cleanup_faults=cleanup(process,thread)
            finally: threading.excepthook=oldhook
        row=dict(case=case,pid=process.pid if process else None,producer_pid=os.getpid(),results=results,
            child_alive=child_alive,reader_alive=reader_alive,parsed_events=events,unhandled=unhandled,
            cleanup_exit=exit_code,reader_retired=thread is not None and not thread.is_alive(),stderr=stderr,handshake=handshake,
            fatal=fatal,cleanup_faults=cleanup_faults)
        (output/(case+'-result.json')).write_text(json.dumps(row,sort_keys=True)+'\n')
        rows.append(row)
        if fatal or cleanup_faults or not child_alive or exit_code!=0 or thread is None or thread.is_alive(): break
    complete=is_complete(rows)
    summary=dict(status='COMPLETE' if complete else 'STOP_CUSTODY_OR_CLEANUP',rows=rows,runtime=runtime,
        timeout_override_seconds=.35,native_runs=1,retries=0)
    (output/'SUMMARY.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(status=summary['status'],cells=len(rows))))
    return 0 if complete else 1

if __name__=='__main__': sys.exit(run(pathlib.Path(sys.argv[1])))
