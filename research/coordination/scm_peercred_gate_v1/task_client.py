import array, json, os, socket, sqlite3, sys

def socket_read(sock_path, key):
    s = socket.socket(socket.AF_UNIX)
    s.connect(sock_path)
    f = s.makefile('rwb')
    f.write((json.dumps({'op':'read','key':key})+'\n').encode()); f.flush()
    out = json.loads(f.readline())
    f.close(); s.close(); return out

def receive_broker_fd(sock_path):
    s = socket.socket(socket.AF_UNIX)
    s.connect(sock_path)
    s.sendall(b'GET\n')
    fds = array.array('i')
    msg, anc, flags, addr = s.recvmsg(1, socket.CMSG_SPACE(fds.itemsize))
    for level, typ, data in anc:
        if level == socket.SOL_SOCKET and typ == socket.SCM_RIGHTS:
            usable = len(data) - (len(data) % fds.itemsize)
            fds.frombytes(data[:usable])
    s.close()
    return msg.decode(errors='replace'), list(fds)

def read_b_from_fd(fd):
    os.lseek(fd,0,0); chunks=[]
    while True:
        b=os.read(fd,65536)
        if not b: break
        chunks.append(b)
    c=sqlite3.connect(':memory:'); c.deserialize(b''.join(chunks))
    v,r=c.execute("select value,revision from kv where key='B'").fetchone(); c.close(); os.close(fd)
    return {'value':v,'revision':r}

def fd_targets():
    out={}
    for name in sorted(os.listdir('/proc/self/fd')):
        try: out[name]=os.readlink('/proc/self/fd/'+name)
        except OSError: pass
    return out

def main():
    owner_sock, broker_sock, db_path = sys.argv[1:4]
    startup = fd_targets()
    a=socket_read(owner_sock,'A')
    path_b=None; path_error=None
    try:
        c=sqlite3.connect(db_path); path_b=c.execute("select value,revision from kv where key='B'").fetchone(); c.close()
    except Exception as e:
        path_error=type(e).__name__
    token={'A':a['revision']}
    if path_b is not None:
        b={'value':path_b[0],'revision':path_b[1]}; source='path'
    else:
        broker_msg, broker_fds = receive_broker_fd(broker_sock)
        if broker_fds:
            b=read_b_from_fd(broker_fds[0])
            for fd in broker_fds[1:]: os.close(fd)
            source='scm_rights_fd'
        else:
            b=socket_read(owner_sock,'B'); token['B']=b['revision']; source='owner_socket'
    out={'uid':os.getuid(),'gid':os.getgid(),'startup_fd_targets':startup,
         'a':a,'b':b,'decision':a['value']+'|'+b['value'],'token':token,
         'raw_path_ok':path_b is not None,'raw_path_error':path_error,'b_source':source,
         'broker_msg':broker_msg if path_b is None else None,
         'broker_fd_count':len(broker_fds) if path_b is None else 0}
    print(json.dumps(out,sort_keys=True))
if __name__=='__main__': main()
