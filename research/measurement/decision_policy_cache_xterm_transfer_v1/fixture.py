from __future__ import annotations
import argparse,json,os,socket,sys,threading,time
from pathlib import Path

VALID='VALID_CONTINUATION'; HARD='HARD_INVALIDATION'
BG={VALID:'42',HARD:'41'}
lock=threading.RLock(); log_lock=threading.Lock()
state=VALID; progress=0; scheduler=None

def emit(path,obj):
    row=dict(obj)
    row.setdefault('t_ns',time.perf_counter_ns())
    with log_lock:
        with path.open('a') as f:
            f.write(json.dumps(row,sort_keys=True)+'\n'); f.flush()

def render():
    code=BG[state]
    sys.stdout.write('\x1b[?25l\x1b[H')
    sys.stdout.write(f'\x1b[{code}m'+' '*40+'\x1b[0m\r\n')
    sys.stdout.write(f'\x1b[{code}m'+' '*40+'\x1b[0m\r\n')
    sys.stdout.write(f'\x1b[0mSTATE={state:<20} PROGRESS={progress:<6}\r\n')
    sys.stdout.flush()

def set_state(log,state_new,case_id,kind):
    global state
    with lock:
        begin=time.perf_counter_ns(); state=state_new; render(); applied=time.perf_counter_ns()
    emit(log,{'event':kind,'case_id':case_id,'state':state_new,'begin_ns':begin,'applied_ns':applied})
    return applied

def sleep_until_ns(target):
    while True:
        rem=target-time.perf_counter_ns()
        if rem<=0:return
        if rem>2_000_000:time.sleep((rem-500_000)/1e9)
        elif rem>100_000:time.sleep(rem/2e9)

def schedule_hard(log,case_id,start_ns,offset_ns):
    target=start_ns+offset_ns; sleep_until_ns(target)
    with lock:
        global state
        begin=time.perf_counter_ns(); state=HARD; render(); applied=time.perf_counter_ns()
    emit(log,{'event':'scheduled_state','case_id':case_id,'state':HARD,'target_ns':target,'begin_ns':begin,'applied_ns':applied})

def reply(conn,obj):
    conn.sendall((json.dumps(obj,sort_keys=True)+'\n').encode())

def main():
    global state,progress,scheduler
    ap=argparse.ArgumentParser()
    ap.add_argument('--socket',required=True);ap.add_argument('--ready',required=True);ap.add_argument('--log',required=True)
    a=ap.parse_args(); sock=Path(a.socket);ready=Path(a.ready);log=Path(a.log)
    sock.parent.mkdir(parents=True,exist_ok=True)
    try:sock.unlink()
    except FileNotFoundError:pass
    srv=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);srv.bind(str(sock));srv.listen(1)
    os.chmod(sock,0o600)
    with lock: render()
    ready.write_text(json.dumps({'pid':os.getpid(),'socket':str(sock),'ready_ns':time.perf_counter_ns()}))
    emit(log,{'event':'ready','pid':os.getpid(),'socket':str(sock)})
    conn,_=srv.accept(); buf=b''; stop=False
    while not stop:
        chunk=conn.recv(65536)
        if not chunk:break
        buf+=chunk
        while b'\n' in buf:
            raw,buf=buf.split(b'\n',1)
            if not raw.strip():continue
            try:
                cmd=json.loads(raw);op=cmd['cmd']
                if op=='set_state':
                    if scheduler is not None and scheduler.is_alive():scheduler.join(timeout=1)
                    applied=set_state(log,cmd['state'],cmd.get('case_id'),'set_state')
                    reply(conn,{'ok':True,'applied_ns':applied})
                elif op=='start_case':
                    if scheduler is not None and scheduler.is_alive():scheduler.join(timeout=1)
                    with lock:
                        progress=0;state=VALID;begin=time.perf_counter_ns();render();applied=time.perf_counter_ns()
                    cid=cmd['case_id'];start_ns=time.perf_counter_ns()+20_000_000
                    emit(log,{'event':'case_reset','case_id':cid,'state':VALID,'begin_ns':begin,'applied_ns':applied,'progress':0})
                    scheduler=threading.Thread(target=schedule_hard,args=(log,cid,start_ns,int(cmd['hard_offset_ns'])),daemon=True);scheduler.start()
                    emit(log,{'event':'case_start','case_id':cid,'start_ns':start_ns,'gap_ns':int(cmd['gap_ns']),'hard_target_ns':start_ns+int(cmd['hard_offset_ns'])})
                    reply(conn,{'ok':True,'start_ns':start_ns})
                elif op=='apply_progress':
                    cid=cmd['case_id'];command_id=cmd['command_id']
                    with lock:
                        recv=time.perf_counter_ns(); before=progress; observed_state=state; accepted=(state==VALID)
                        if accepted:progress+=1
                        after=progress
                        if accepted:render()
                        effect=time.perf_counter_ns()
                    emit(log,{'event':'apply_result','case_id':cid,'command_id':command_id,'recv_ns':recv,'effect_ns':effect,'state_at_recv':observed_state,'accepted':accepted,'progress_before':before,'progress_after':after})
                    reply(conn,{'ok':True,'command_id':command_id})
                elif op=='end_case':
                    if scheduler is not None:scheduler.join(timeout=1)
                    with lock:snap={'state':state,'progress':progress,'snapshot_ns':time.perf_counter_ns()}
                    emit(log,{'event':'case_end','case_id':cmd['case_id'],**snap});reply(conn,{'ok':True,**snap})
                elif op=='exit':
                    if scheduler is not None:scheduler.join(timeout=1)
                    emit(log,{'event':'exit'});reply(conn,{'ok':True});stop=True
                else:raise ValueError('unknown command')
            except Exception as e:
                emit(log,{'event':'error','error':f'{type(e).__name__}: {e}'})
                reply(conn,{'ok':False,'error':f'{type(e).__name__}: {e}'})
    try:conn.close()
    except Exception:pass
    srv.close()
    try:sock.unlink()
    except FileNotFoundError:pass
    sys.stdout.write('\x1b[?25h');sys.stdout.flush()

if __name__=='__main__':main()
