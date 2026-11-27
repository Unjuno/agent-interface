"""Disposable Windows pipe probe; no GUI or input."""
import json,multiprocessing as mp,threading,time

def sink(reader,ready,stop):
    ready.set()
    stop.wait(5)
    reader.close()

def main():
    ctx=mp.get_context("spawn");reader,writer=ctx.Pipe(duplex=False);ready=ctx.Event();stop=ctx.Event()
    child=ctx.Process(target=sink,args=(reader,ready,stop));child.start();reader.close()
    entered=threading.Event();finished=threading.Event();result=[]
    def send():
        entered.set()
        try: writer.send_bytes(b"x"*(8*1024*1024));result.append("sent")
        except BaseException as error: result.append(type(error).__name__)
        finally: finished.set()
    t=threading.Thread(target=send,daemon=True)
    try:
        if not ready.wait(3): raise RuntimeError("child not ready")
        t.start()
        if not entered.wait(1): raise RuntimeError("send not started")
        blocked=not finished.wait(.25)
        start=time.monotonic_ns();child.terminate();child.join(2)
        exited=not child.is_alive();unblocked=finished.wait(2)
        elapsed=time.monotonic_ns()-start
        print(json.dumps({"schema":"owned-pipe-blocked-peer-v1","payload_bytes":8*1024*1024,"blocked_before_termination":blocked,"child_exited":exited,"sender_unblocked":unblocked,"sender_result":result,"termination_and_unblock_ns":elapsed,"scope":"owned disposable process and local pipe; no GUI or OS input"}))
        return 0 if blocked and exited and unblocked and result != ["sent"] else 1
    finally:
        stop.set()
        if child.is_alive(): child.terminate();child.join(2)
        writer.close()
        t.join(2)

if __name__=="__main__":raise SystemExit(main())
