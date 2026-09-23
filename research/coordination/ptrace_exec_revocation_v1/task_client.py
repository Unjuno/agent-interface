import array,json,os,socket,sqlite3,sys

def socket_read(path,key):
    s=socket.socket(socket.AF_UNIX); s.connect(path); f=s.makefile('rwb')
    f.write((json.dumps({'op':'read','key':key})+'\n').encode()); f.flush(); out=json.loads(f.readline()); f.close(); s.close(); return out

def recv_cap(fd):
    try: s=socket.socket(fileno=fd)
    except OSError as e: return {'fd_exists':False,'usable':False,'error':type(e).__name__,'fds':[]}
    try:
        try: s.sendall(b'GET\n')
        except OSError as e: return {'fd_exists':True,'usable':False,'error':type(e).__name__,'fds':[]}
        fds=array.array('i')
        try: msg,anc,flags,addr=s.recvmsg(1,socket.CMSG_SPACE(fds.itemsize))
        except OSError as e: return {'fd_exists':True,'usable':False,'error':type(e).__name__,'fds':[]}
        for level,typ,data in anc:
            if level==socket.SOL_SOCKET and typ==socket.SCM_RIGHTS:
                usable=len(data)-(len(data)%fds.itemsize); fds.frombytes(data[:usable])
        return {'fd_exists':True,'usable':bool(fds),'error':None,'fds':list(fds),'msg':msg.decode(errors='replace')}
    finally: s.close()

def read_b_fd(fd):
    os.lseek(fd,0,0); buf=[]
    while True:
        x=os.read(fd,65536)
        if not x: break
        buf.append(x)
    c=sqlite3.connect(':memory:'); c.deserialize(b''.join(buf)); v,r=c.execute("select value,revision from kv where key='B'").fetchone(); c.close(); os.close(fd); return {'value':v,'revision':r}

def main():
    owner,db,alias_s,helper_pid_s=sys.argv[1:5]; alias=int(alias_s); helper_pid=int(helper_pid_s)
    a=socket_read(owner,'A'); token={'A':a['revision']}
    try:
        c=sqlite3.connect(db); raw=c.execute("select value,revision from kv where key='B'").fetchone();c.close();raw_ok=True;raw_err=None
    except Exception as e: raw_ok=False;raw=None;raw_err=type(e).__name__
    cap=recv_cap(alias)
    if raw_ok: b={'value':raw[0],'revision':raw[1]};src='raw_path'
    elif cap['fds']:
        b=read_b_fd(cap['fds'][0]); [os.close(x) for x in cap['fds'][1:]]; src='delegated_cap_scm_rights'
    else:
        b=socket_read(owner,'B'); token['B']=b['revision']; src='owner_socket'
    print(json.dumps({'pid':os.getpid(),'helper_pid_arg':helper_pid,'same_pid_after_exec':os.getpid()==helper_pid,'uid':os.getuid(),'gid':os.getgid(),'raw_path_ok':raw_ok,'raw_path_error':raw_err,'cap_fd_exists':cap['fd_exists'],'cap_usable':cap['usable'],'cap_error':cap['error'],'cap_fd_count':len(cap['fds']),'b_source':src,'a':a,'b':b,'decision':a['value']+'|'+b['value'],'token':token},sort_keys=True))
if __name__=='__main__':main()
