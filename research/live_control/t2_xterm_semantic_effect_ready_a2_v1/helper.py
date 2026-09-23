#!/usr/bin/env python3
import argparse,json,os,pathlib,termios,time,tty
p=argparse.ArgumentParser()
p.add_argument('--ready',required=True); p.add_argument('--byte-out',required=True); p.add_argument('--semantic-out',required=True)
p.add_argument('--session-id',required=True); p.add_argument('--request-id',required=True); p.add_argument('--delay-ms',type=float,required=True)
p.add_argument('--no-effect',action='store_true')
a=p.parse_args(); fd=0; old=termios.tcgetattr(fd); tty.setraw(fd)
def atomic(path,obj):
    dst=pathlib.Path(path); tmp=dst.with_suffix(dst.suffix+'.tmp'); tmp.write_text(json.dumps(obj,sort_keys=True)); os.replace(tmp,dst)
try:
    atomic(a.ready,{'ready_ns':time.perf_counter_ns(),'pid':os.getpid(),'session_id':a.session_id,'request_id':a.request_id})
    b=os.read(fd,1); recv=time.perf_counter_ns()
    atomic(a.byte_out,{'recv_ns':recv,'byte_hex':b.hex(),'byte_int':b[0] if b else None,'count':len(b),'session_id':a.session_id,'request_id':a.request_id})
    if not a.no_effect and b==b'x':
        target=recv+int(a.delay_ms*1_000_000)
        while True:
            now=time.perf_counter_ns()
            if now>=target: break
            time.sleep(min((target-now)/1e9,0.0005))
        atomic(a.semantic_out,{
            'session_id':a.session_id,'request_id':a.request_id,'role':'TASK_SEMANTIC_EFFECT','accepted_key':'x','result':'TOKEN_ACCEPTED',
            'effect_ns':time.perf_counter_ns(),'input_authority':False,'semantic_authority':False})
finally:
    termios.tcsetattr(fd,termios.TCSADRAIN,old)
