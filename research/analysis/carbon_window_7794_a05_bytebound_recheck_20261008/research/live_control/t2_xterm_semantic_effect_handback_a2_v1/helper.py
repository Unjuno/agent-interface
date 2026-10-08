#!/usr/bin/env python3
import argparse,json,os,pathlib,termios,time,tty
p=argparse.ArgumentParser(); p.add_argument('--ready',required=True); p.add_argument('--input',required=True); p.add_argument('--effect',required=True); p.add_argument('--session',required=True); p.add_argument('--request',required=True); p.add_argument('--delay-ms',type=float,required=True); p.add_argument('--no-effect',action='store_true'); a=p.parse_args()
fd=0; old=termios.tcgetattr(fd); tty.setraw(fd)
def atomic(path,obj):
    dst=pathlib.Path(path); tmp=dst.with_suffix(dst.suffix+'.tmp'); tmp.write_text(json.dumps(obj,sort_keys=True)); os.replace(tmp,dst)
try:
    atomic(a.ready,{'ready_ns':time.perf_counter_ns(),'pid':os.getpid(),'session_id':a.session})
    b=os.read(fd,1); recv=time.perf_counter_ns()
    atomic(a.input,{'recv_ns':recv,'byte_hex':b.hex(),'count':len(b),'session_id':a.session,'request_id':a.request})
    if not a.no_effect and b==b'x':
        target=recv+int(a.delay_ms*1e6)
        while time.perf_counter_ns()<target: time.sleep(0.0001)
        atomic(a.effect,{'effect_ns':time.perf_counter_ns(),'session_id':a.session,'request_id':a.request,'role':'TASK_SEMANTIC_EFFECT','accepted_key':'x','result':'TOKEN_ACCEPTED','input_authority':False,'semantic_authority':False})
finally:
    termios.tcsetattr(fd,termios.TCSADRAIN,old)
