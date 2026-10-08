import argparse,array,json,os,pathlib,socket,sqlite3,subprocess,threading,struct
SCHEMA='''
create table kv(key text primary key, value text not null, revision integer not null);
create table coordination(generation integer not null);
create table events(kind text not null, generation integer not null);
insert into kv values('A','a1',1),('B','b1',1);
insert into coordination values(1);
'''

def handle_owner(csock, db_path):
    f=csock.makefile('rwb')
    for line in f:
        req=json.loads(line); con=sqlite3.connect(db_path,isolation_level=None)
        if req['op']=='read':
            value,revision=con.execute('select value,revision from kv where key=?',(req['key'],)).fetchone(); out={'value':value,'revision':revision}
        else: out={'error':'unsupported'}
        con.close(); f.write((json.dumps(out,sort_keys=True)+'\n').encode()); f.flush()
    f.close(); csock.close()

def start_owner(sock_path, db_path):
    ready=threading.Event(); stop=threading.Event()
    def server():
        if sock_path.exists(): sock_path.unlink()
        s=socket.socket(socket.AF_UNIX); s.bind(str(sock_path)); os.chmod(sock_path,0o666); s.listen(); s.settimeout(0.1); ready.set()
        while not stop.is_set():
            try: c,_=s.accept()
            except TimeoutError: continue
            threading.Thread(target=handle_owner,args=(c,db_path),daemon=True).start()
        s.close()
    t=threading.Thread(target=server,daemon=True); t.start(); ready.wait(2); return stop,t

def start_broker(sock_path, db_path, arm):
    ready=threading.Event(); stop=threading.Event(); record={'connections':0,'sent_fd':False}
    def server():
        if sock_path.exists(): sock_path.unlink()
        s=socket.socket(socket.AF_UNIX); s.bind(str(sock_path)); os.chmod(sock_path,0o666); s.listen(); s.settimeout(0.1); ready.set()
        while not stop.is_set():
            try: c,_=s.accept()
            except TimeoutError: continue
            record['connections']+=1
            cred=c.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,struct.calcsize('3i'))
            peer_pid,peer_uid,peer_gid=struct.unpack('3i',cred)
            record['peer_pid']=peer_pid; record['peer_uid']=peer_uid; record['peer_gid']=peer_gid
            _=c.recv(16)
            allow = arm=='unguarded' or peer_uid==0
            record['allowed']=allow
            if allow:
                fd=os.open(db_path,os.O_RDONLY); fds=array.array('i',[fd]); c.sendmsg([b'F'],[(socket.SOL_SOCKET,socket.SCM_RIGHTS,fds)]); os.close(fd); record['sent_fd']=True
            else:
                c.sendmsg([b'D'])
            c.close()
        s.close()
    t=threading.Thread(target=server,daemon=True); t.start(); ready.wait(2); return stop,t,record

def commit_with_token(db_path, token):
    con=sqlite3.connect(db_path,isolation_level=None); con.execute('begin immediate'); mm=[]
    for key,exp in sorted(token.items()):
        act=con.execute('select revision from kv where key=?',(key,)).fetchone()[0]
        if act!=exp: mm.append({'key':key,'expected':exp,'actual':act})
    if mm: con.execute('rollback'); committed=False
    else:
        con.execute('update coordination set generation=2'); con.execute("insert into events values('generation_commit',2)"); con.execute('commit'); committed=True
    con.close(); return committed,mm

def snapshot(db_path):
    con=sqlite3.connect(db_path); kv={k:{'value':v,'revision':r} for k,v,r in con.execute('select key,value,revision from kv order by key')}; g=con.execute('select generation from coordination').fetchone()[0]; ev=[list(x) for x in con.execute('select kind,generation from events order by rowid')]; con.close(); return {'kv':kv,'generation':g,'events':ev}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--arm',choices=['unguarded','peer_guard'],required=True); ap.add_argument('--scenario',choices=['stable','B_change'],required=True); ap.add_argument('--case-id',required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
    out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=False); os.chmod(out,0o755)
    private=out/'private'; public=out/'public'; private.mkdir(); public.mkdir(); os.chmod(private,0o700); os.chmod(public,0o777)
    db=private/'state.db'; owner_sock=public/'owner.sock'; broker_sock=public/'broker.sock'
    con=sqlite3.connect(db); con.executescript(SCHEMA); con.commit(); con.close(); os.chmod(db,0o600)
    os_stop,os_thr=start_owner(owner_sock,db); br_stop,br_thr,broker_record=start_broker(broker_sock,db,args.arm)
    task=pathlib.Path(__file__).with_name('task_client.py')
    cmd=['setpriv','--reuid=65534','--regid=65534','--clear-groups','python3',str(task),str(owner_sock),str(broker_sock),str(db)]
    proc=subprocess.run(cmd,capture_output=True,text=True,check=False,timeout=10)
    if proc.returncode!=0: raise RuntimeError(f'task rc={proc.returncode} stderr={proc.stderr}')
    task_result=json.loads(proc.stdout)
    if args.scenario=='B_change':
        con=sqlite3.connect(db); con.execute("update kv set value='b2',revision=2 where key='B'"); con.commit(); con.close()
    committed,mm=commit_with_token(db,task_result['token']); final=snapshot(db); st=os.stat(db); pst=os.stat(private)
    result={'case_id':args.case_id,'arm':args.arm,'scenario':args.scenario,'task':task_result,'broker':broker_record,'committed':committed,'mismatches':mm,'final':final,
            'db_mode':oct(st.st_mode&0o777),'db_uid':st.st_uid,'private_mode':oct(pst.st_mode&0o777),'private_uid':pst.st_uid,'task_returncode':proc.returncode,'task_stderr":proc.stderr}
    (out/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    os_stop.set(); br_stop.set(); os_thr.join(1); br_thr.join(1)
    for p in [owner_sock,broker_sock]:
        if p.exists(): p.unlink()
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
