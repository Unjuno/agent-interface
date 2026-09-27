import json, os, socket, sqlite3, sys

def socket_read(sock_path, key):
    s=socket.socket(socket.AF_UNIX); s.connect(sock_path)
    f=s.makefile('rwb'); f.write((json.dumps({'op':'read','key':key})+'\n').encode()); f.flush()
    out=json.loads(f.readline()); f.close(); s.close(); return out

def read_b_from_fd(fd):
    os.lseek(fd,0,0); chunks=[]
    while True:
        b=os.read(fd,65536)
        if not b: break
        chunks.append(b)
    c=sqlite3.connect(':memory:'); c.deserialize(b''.join(chunks))
    v,r=c.execute("select value,revision from kv where key='B'").fetchone(); c.close()
    return {'value':v,'revision':r}

def main():
    sock_path, db_path = sys.argv[1:3]
    a=socket_read(sock_path,'A')
    path_b=None; path_error=None
    try:
        c=sqlite3.connect(db_path); path_b=c.execute("select value,revision from kv where key='B'").fetchone(); c.close()
    except Exception as e:
        path_error=type(e).__name__
    token={'A':a['revision']}
    source='path' if path_b is not None else None
    if path_b is not None:
        b={'value':path_b[0],'revision':path_b[1]}
    else:
        leak=os.environ.get('LEAK_FD')
        if leak is not None:
            b=read_b_from_fd(int(leak)); source='fd_deserialize'
        else:
            b=socket_read(sock_path,'B'); token['B']=b['revision']; source='socket'
    out={'uid':os.getuid(),'gid':os.getgid(),'a':a,'b':b,'decision':a['value']+'|'+b['value'],
         'token':token,'raw_path_ok':path_b is not None,'raw_path_error':path_error,'b_source':source,
         'leak_fd_present':os.environ.get('LEAK_FD') is not None}
    print(json.dumps(out,sort_keys=True))
if __name__=='__main__': main()
