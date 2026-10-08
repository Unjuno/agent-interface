#!/opt/pyvenv/bin/python3
import argparse,json,os,pathlib,socket,termios,time,tty
p=argparse.ArgumentParser()
p.add_argument('--ready',required=True); p.add_argument('--input',required=True)
p.add_argument('--transport',choices=['file','dgram'],required=True)
p.add_argument('--effect-file'); p.add_argument('--sock'); p.add_argument('--session',required=True); p.add_argument('--request',required=True)
p.add_argument('--delay-ms',type=float,default=13.0)
a=p.parse_args()

def atomic(path,obj):
    dst=pathlib.Path(path); tmp=dst.with_suffix(dst.suffix+'.tmp')
    tmp.write_text(json.dumps(obj,sort_keys=True)); os.replace(tmp,dst)
fd=0; old=termios.tcgetattr(fd); tty.setraw(fd)
try:
    atomic(a.ready,{'ready_ns':time.perf_counter_ns(),'pid':os.getpid()})
    b=os.read(fd,1); recv_ns=time.perf_counter_ns()
    atomic(a.input,{'recv_ns':recv_ns,'byte_hex':b.hex(),'count':len(b)})
    target=recv_ns+int(a.delay_ms*1e6)
    while True:
        now=time.perf_counter_ns()
        if now>=target: break
        rem=(target-now)/1e9
        if rem>0.001: time.sleep(rem-0.0005)
    effect_ns=time.perf_counter_ns()
    row={'effect_ns':effect_ns,'session_id':a.session,'request_id':a.request,'role':'TASK_SEMANTIC_EFFECT','accepted_key':'x','result':'TOKEN_ACCEPTED','input_authority':False,'semantic_authority':False}
    payload=json.dumps(row,sort_keys=True).encode()
    if a.transport=='file':
        atomic(a.effect_file,row)
    else:
        s=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
        try: s.sendto(payload,a.sock)
        finally: s.close()
finally:
    termios.tcsetattr(fd,termios.TCSADRAIN,old)
