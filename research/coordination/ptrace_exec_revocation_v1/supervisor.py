import argparse,ctypes,json,os,socket,subprocess,sys
PTRACE_SEIZE=0x4206; PTRACE_CONT=7; PTRACE_O_TRACEEXEC=0x10; PTRACE_EVENT_EXEC=4
libc=ctypes.CDLL(None,use_errno=True); libc.ptrace.argtypes=[ctypes.c_ulong,ctypes.c_ulong,ctypes.c_void_p,ctypes.c_void_p];libc.ptrace.restype=ctypes.c_long

def ptrace(req,pid,data=0):
    r=libc.ptrace(req,pid,ctypes.c_void_p(0),ctypes.c_void_p(data))
    if r==-1:
        e=ctypes.get_errno(); raise OSError(e,os.strerror(e))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--arm',choices=['no_observer','ptrace_exec_revoke'],required=True);ap.add_argument('--cap-fd',type=int,required=True);ap.add_argument('--ctrl-fd',type=int,required=True);ap.add_argument('--helper',required=True);ap.add_argument('--task',required=True);ap.add_argument('--owner',required=True);ap.add_argument('--db',required=True);a=ap.parse_args()
    rr,rw=os.pipe();gr,gw=os.pipe()
    p=subprocess.Popen([sys.executable,a.helper,str(a.cap_fd),a.task,a.owner,a.db,str(rw),str(gr)],pass_fds=(a.cap_fd,rw,gr),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    os.close(rw);os.close(gr)
    if os.read(rr,1)!=b'R': raise RuntimeError('no ready')
    os.close(rr)
    trace={'seize':False,'exec_stop':False,'event':None,'stop_signal':None}
    if a.arm=='ptrace_exec_revoke':
        ptrace(PTRACE_SEIZE,p.pid,PTRACE_O_TRACEEXEC);trace['seize']=True
    os.write(gw,b'G');os.close(gw)
    ctrl=socket.socket(fileno=a.ctrl_fd)
    if a.arm=='ptrace_exec_revoke':
        wp,st=os.waitpid(p.pid,0);trace['event']=st>>16;trace['stop_signal']=os.WSTOPSIG(st) if os.WIFSTOPPED(st) else None
        if not (os.WIFSTOPPED(st) and (st>>16)==PTRACE_EVENT_EXEC): raise RuntimeError(f'bad ptrace stop {hex(st)}')
        trace['exec_stop']=True
        ctrl.sendall(b'EXEC\n')
        if ctrl.recv(16)!=b'ACK\n': raise RuntimeError('bad ack')
        ptrace(PTRACE_CONT,p.pid,0)
        trace['post_exec_stops']=[]
        while True:
            wp,st=os.waitpid(p.pid,0)
            if os.WIFEXITED(st):
                p.returncode=os.WEXITSTATUS(st); break
            if os.WIFSIGNALED(st):
                p.returncode=-os.WTERMSIG(st); break
            if os.WIFSTOPPED(st):
                sig=os.WSTOPSIG(st); trace['post_exec_stops'].append(sig)
                # CPython ignores SIGPIPE by default; suppress the ptrace delivery to preserve that behavior.
                deliver=0 if sig==13 else sig
                ptrace(PTRACE_CONT,p.pid,deliver); continue
            raise RuntimeError(f'bad child state {hex(st)}')
        stdout=p.stdout.read();stderr=p.stderr.read()
    else:
        stdout,stderr=p.communicate(timeout=10)
    ctrl.close()
    if p.returncode: raise RuntimeError(stderr)
    print(json.dumps({'helper_pid':p.pid,'trace':trace,'task':json.loads(stdout),'stderr':stderr},sort_keys=True))
if __name__=='__main__':main()
