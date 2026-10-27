"""Owned process and pipe diagnostic; no native GUI or input."""
import json, multiprocessing as mp, os, subprocess, sys, threading, time
from pathlib import Path

def emit(path, stage, **fields):
    row={"stage":stage,"monotonic_ns":time.monotonic_ns(),**fields}
    with open(path,"a",encoding="utf-8",newline="\n") as f:
        f.write(json.dumps(row,sort_keys=True)+"\n");f.flush();os.fsync(f.fileno())

def worker(root):
    trace=root/"worker_trace.jsonl"
    emit(trace,"worker_start",pid=os.getpid())
    reader,writer=mp.Pipe(duplex=False)
    emit(trace,"pipe_created")
    entered=threading.Event();finished=threading.Event(); outcome=[]
    def send():
        emit(trace,"send_entered");entered.set()
        try: writer.send_bytes(b"x"*(8*1024*1024));outcome.append("sent")
        except BaseException as e: outcome.append(type(e).__name__)
        finally: emit(trace,"send_finished",outcome=outcome);finished.set()
    t=threading.Thread(target=send,daemon=True);t.start()
    if not entered.wait(1): emit(trace,"send_not_entered");return 2
    done_before_close=finished.wait(.25)
    emit(trace,"before_reader_close",send_finished=done_before_close)
    reader.close()
    emit(trace,"reader_closed")
    finished_after_close=finished.wait(1)
    emit(trace,"after_reader_close",send_finished=finished_after_close,outcome=outcome)
    if finished_after_close: writer.close();emit(trace,"writer_closed")
    return 0 if not done_before_close and finished_after_close and outcome != ["sent"] else 3

def main(root):
    root.mkdir(parents=True,exist_ok=False)
    kwargs={"stdin":subprocess.DEVNULL,"creationflags":getattr(subprocess,"CREATE_NO_WINDOW",0)}
    start=time.monotonic_ns()
    with open(root/"stdout.bin","xb") as out, open(root/"stderr.bin","xb") as err:
        child=subprocess.Popen([sys.executable,"-B",__file__,"worker",str(root)],stdout=out,stderr=err,**kwargs)
        emit(root/"supervisor_trace.jsonl","child_started",pid=child.pid)
        timed_out=False
        try: code=child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            timed_out=True;emit(root/"supervisor_trace.jsonl","deadline_expired",pid=child.pid)
            child.kill()
            try: code=child.wait(timeout=3)
            except subprocess.TimeoutExpired: code=None
        emit(root/"supervisor_trace.jsonl","child_wait_complete",exit_code=code,timed_out=timed_out)
    row={"schema":"owned-pipe-r02-v1","pid":child.pid,"exit_code":code,"timed_out":timed_out,"child_exited":child.poll() is not None,"elapsed_ns":time.monotonic_ns()-start,"scope":"one owned subprocess; same-process pipe ends; no GUI or input"}
    (root/"RESULT.json").write_text(json.dumps(row,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(row,sort_keys=True));return 0 if row["child_exited"] else 2

if __name__=="__main__":
    if len(sys.argv)==3 and sys.argv[1]=="worker": raise SystemExit(worker(Path(sys.argv[2])))
    if len(sys.argv)==2: raise SystemExit(main(Path(sys.argv[1])))
    raise SystemExit("expected fresh output directory")
