#!/usr/bin/env python3
import argparse,json,os,pathlib,termios,time,tty
p=argparse.ArgumentParser(); p.add_argument('--ready',required=True); p.add_argument('--receipt',required=True); p.add_argument('--session',required=True); p.add_argument('--request',required=True); p.add_argument('--delay-ms',type=float,required=True); p.add_argument('--effect-enabled',type=int,choices=[0,1],required=True); a=p.parse_args()
fd=0; old=termios.tcgetattr(fd); tty.setraw(fd)
try:
    pathlib.Path(a.ready).write_text(json.dumps({'ready_ns':time.perf_counter_ns(),'pid':os.getpid()},sort_keys=True))
    b=os.read(fd,1); recv=time.perf_counter_ns()
    if b==b'x' and a.effect_enabled:
        time.sleep(a.delay_ms/1000); effect=time.perf_counter_ns()
        row={'kind':'TASK_RECEIPT','role':'TASK_SEMANTIC_EFFECT','session_id':a.session,'request_id':a.request,'accepted_key':'x','result':'TOKEN_ACCEPTED','received_ns':recv,'effect_ns':effect,'input_authority':False,'semantic_authority':False}
        dst=pathlib.Path(a.receipt); tmp=dst.with_suffix('.tmp'); tmp.write_text(json.dumps(row,sort_keys=True),encoding='utf-8'); os.replace(tmp,dst)
finally:
    termios.tcsetattr(fd,termios.TCSADRAIN,old)
