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
from core import extract, judge

def cleanup(process, thread):
    faults=[]
    exit_code=None
    stderr=''
    def attempt(label, fn):
        try: return fn()
        except Exception as exc:
            faults.append(dict(step=label,error=repr(exc)))
    if process is not None:
        attempt('stdin-close',process.stdin.close)
        try: exit_code=process.wait(timeout=5)
        except Exception as exc:
            faults.append(dict(step='wait',error=repr(exc)))
            attempt('kill',process.kill)
            exit_code=attempt('wait-after-kill',lambda:process.wait(timeout=5))
    if thread is not None:
        attempt('reader-join',lambda:thread.join(timeout=2))
    if process is not None:
        terminal=attempt('poll',process.poll)
        retired=thread is None or not thread.is_alive()
        if terminal is not None:
            stderr=attempt('stderr-read',process.stderr.read)
        if terminal is not None and retired:
            for name in ('stdout','stderr'):
                attempt(name+'-close',getattr(process,name).close)
        else:
            faults.append(dict(step='pipe-close-deferred',error='unreaped child or live reader; avoid blocking stream lock; STOP and container teardown required'))
    return exit_code,stderr,faults

def run(out):
    out.mkdir(parents=True, exist_ok=False)
    root=pathlib.Path(__file__).resolve().parent
    source=(root/'source/v39.py.txt').read_bytes()
    factory, identity=extract(source)
    limits={}
    for name in ('cpu.max','memory.max','memory.swap.max','pids.max'):
        limits[name]=pathlib.Path('/sys/fs/cgroup',name).read_text().strip()
    if limits != {'cpu.max':'100000 100000','memory.max':'536870912','memory.swap.max':'0','pids.max':'64'} or os.getuid()!=501:
        raise RuntimeError('allocation limits mismatch')
    (out/'RUNTIME.json').write_text(json.dumps(dict(uid=os.getuid(),pid=os.getpid(),
        limits=limits,cgroup=pathlib.Path('/proc/self/cgroup').read_text(),
        utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())),sort_keys=True)+'\n')
    (out/'source-identity.json').write_text(json.dumps(identity,sort_keys=True)+'\n')
    rows=[]
    for case in ('healthy','malformed','array'):
        errors=[]
        error_details=[]
        oldhook=threading.excepthook
        def hook(args):
            errors.append(args.exc_type.__name__)
            error_details.append(dict(type=args.exc_type.__name__, message=str(args.exc_value),
                doc=getattr(args.exc_value,'doc',None), thread=args.thread.name,
                monotonic_ns=time.monotonic_ns(), traceback=''.join(traceback.format_exception(
                    args.exc_type,args.exc_value,args.exc_traceback))))
        process=None
        thread=None
        events=[]
        elapsed=None
        child_alive=False
        reader_alive=False
        fatal=None
        outcome='unclassified'
        detail=None
        cleanup_exit=None
        try:
            process=subprocess.Popen([sys.executable,'-B',str(root/'peer.py'),case,str(out/(case+'-peer.json'))],
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
            incoming=queue.Queue()
            reader,wait,events=factory(process,incoming)
            thread=threading.Thread(target=reader,daemon=True,name='v39-reader-'+case)
            threading.excepthook=hook
            thread.start()
            start=time.monotonic_ns()
            try:
                result=wait(lambda r:r['event']=='ready',timeout=.35)
                outcome=result.get('event','other')
                detail=result
            except Exception as exc:
                outcome=type(exc).__name__
                detail=dict(message=str(exc),traceback=traceback.format_exc())
            elapsed=time.monotonic_ns()-start
            child_alive=process.poll() is None
            reader_alive=thread.is_alive()
        except Exception as exc:
            fatal=dict(error=repr(exc),traceback=traceback.format_exc())
        finally:
            try:
                cleanup_exit,stderr,cleanup_faults=cleanup(process,thread)
            finally:
                threading.excepthook=oldhook
        row=dict(case=case,pid=process.pid if process else None,producer_pid=os.getpid(),
            fatal=fatal,cleanup_faults=cleanup_faults,outcome=outcome,detail=detail,elapsed_ns=elapsed,
            child_alive=child_alive,reader_alive=reader_alive,cleanup_exit=cleanup_exit,
            reader_retired=thread is not None and not thread.is_alive(),errors=errors,error_details=error_details,
            parsed_events=events,stderr=stderr)
        (out/(case+'-result.json')).write_text(json.dumps(row,sort_keys=True)+'\n')
        rows.append(row)
        if fatal or cleanup_faults or not child_alive or cleanup_exit != 0 or thread is None or thread.is_alive():
            break
    verdict=judge(rows)
    summary=dict(verdict=verdict,rows=rows,source=identity,producer_uid=os.getuid(),
        scope='AST reader/wait subset; real owned pipes; no full controller/game/model',
        timeout_override_seconds=.35,default_timeout_seconds=40)
    (out/'SUMMARY.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(verdict=verdict,cells=len(rows))))
    return 0 if len(rows)==3 and not verdict.startswith('STOP') else 1

if __name__=='__main__':
    sys.exit(run(pathlib.Path(sys.argv[1])))
