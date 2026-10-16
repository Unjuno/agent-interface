#!/usr/bin/env python3
import argparse,json,os,pathlib,termios,time,tty
p=argparse.ArgumentParser(); p.add_argument('--ready',required=True); p.add_argument('--out',required=True); a=p.parse_args()
fd=0; old=termios.tcgetattr(fd); tty.setraw(fd)
try:
    pathlib.Path(a.ready).write_text(json.dumps({'ready_ns':time.perf_counter_ns(),'pid':os.getpid()}))
    b=os.read(fd,1); recv=time.perf_counter_ns()
    row={'recv_ns':recv,'byte_hex':b.hex(),'byte_int':b[0] if b else None,'count':len(b)}
    dst=pathlib.Path(a.out); tmp=dst.with_suffix('.tmp'); tmp.write_text(json.dumps(row,sort_keys=True)); os.replace(tmp,dst)
finally:
    termios.tcsetattr(fd,termios.TCSADRAIN,old)
