import array, json, os, socket, sqlite3, sys

def socket_read(sock_path, key):
    s=socket.socket(socket.AF_UNIX); s.connect(sock_path); f=s.makefile('rwb')
    f.write((json.dumps({'op':'read','key':key})+'\n').encode()); f.flush(); out=json.loads(f.readline()); f.close(); s.close(); return out

def receive_cap_fd(cap_fd):
    try: s=socket.socket(fileno=cap_fd)
    except OSError as e: return {'fd_exists':False,'usable':False,'error':type(e).__name__,'msg':None,'fds':[]}
    try:
        try: s.sendall(b'GET\n')
        except OSError as e: return {'fd_exists':True,'usable':False,'error':type(e).__name__,'msg':None,'fds':[]}
        fds=array.array('i')
        try: msg,anc,flags,addr=s.recvmsg(1,socket.CMSG_SPACE(fds.itemsize))
        except OSError as e: return {'fd_exists':True,'usable':False,'error':type(e).__name__,'msg':None,'fds':[]}
        for level,typ,data in anc:
            if level==socket.SOL_SOCKET and typ==socket.SCM_RIGHTS:
                usable=len(data)-(len(data)%fds.itemsize); fds.frombytes(data[:usable])
        return {'fd_exists':True,'usable':bool(fds),'error':None,'msg':msg.decode(errors='replace'),'fds':list(fds)}
    finally:
        s.close()

def read_b_from_fd(fd):
    os.lseek(fd,0,0); chunks=[]
    while True:
        b=os.read(fd,65536)
        if not b: break
        chunks.append(b)
    c=sqlite3.connect(':memory:'); c.deserialize(b''.join(chunks)); v,r=c.execute("select value,revision from kv where key='B'").fetchone(); c.close(); os.close(fd); return {'value':v,'revision':r}

def main():
    owner_sock,db_path,cap_alias_s,helper_pid_s=sys.argv[1:5]; fd=int(cap_alias_s); helper_pid=int(helper_pid_s)
    a=socket_read(owner_sock,'A'); token={'A':a['revision']}
    try:
        c=sqlite3.connect(db_path); raw=c.execute("select value,revision from kv where key='B'").fetchone(); c.close(); raw_ok=True; raw_err=None
    except Exception as e: raw_ok=False; raw=None; raw_err=type(e).__name__
    cap=receive_cap_fd(fd)
    if raw_ok: b={'value':raw[0],'revision':raw[1]}; src='raw_path'
    elif cap['fds']:
        b=read_b_from_fd(cap['fds'][0]); [os.close(x) for x in cap['fds'][1:]]; src='delegated_cap_scm_rights'
    else:
        b=socket_read(owner_sock,'B'); token['B']=b['revision']; src='owner_socket'
    print(json.dumps({'pid':os.getpid(),'helper_pid_arg':helper_pid,'same_pid_after_exec':os.getpid()==helper_pid,'uid':os.getuid(),'gid':os.getgid(),'raw_path_ok':raw_ok,'raw_path_error':raw_err,'cap_fd_exists':cap['fd_exists'],'cap_usable':cap['usable'],'cap_error':cap['error'],'cap_msg':cap['msg'],'cap_fd_count':len(cap['fds']),'a':a,'b':b,'b_source':src,'decision':a['value']+'|'+b['value'],'token':token},sort_keys=True))
if __name__=='__main__': main()
