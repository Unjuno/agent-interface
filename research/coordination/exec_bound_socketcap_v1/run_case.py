import argparse,array,json,os,pathlib,socket,sqlite3,subprocess,threading,time

SCHEMA='''
create table kv(key text primary key, value text not null, revision integer not null);
create table coordination(generation integer not null);
create table events(kind text not null, generation integer not null);
insert into kv values('A','a1',1),('B','b1',1);
insert into coordination values(1);
'''

def handle_owner(c,db):
    f=c.makefile('rwb')
    for line in f:
        q=json.loads(line); con=sqlite3.connect(db)
        v,r=con.execute('select value,revision from kv where key=?',(q['key'],)).fetchone(); con.close()
        f.write((json.dumps({'value':v,'revision':r},sort_keys=True)+'\n').encode()); f.flush()
    f.close(); c.close()

def start_owner(path,db):
    ready=threading.Event(); stop=threading.Event(); rec={'reads':[]}
    def server():
        if path.exists(): path.unlink()
        s=socket.socket(socket.AF_UNIX); s.bind(str(path)); os.chmod(path,0o666); s.listen(); s.settimeout(.1); ready.set()
        while not stop.is_set():
            try: c,_=s.accept()
            except TimeoutError: continue
            # wrapper records request keys while serving
            def serve(cc):
                f=cc.makefile('rwb')
                for line in f:
                    q=json.loads(line); rec['reads'].append(q['key']); con=sqlite3.connect(db)
                    v,r=con.execute('select value,revision from kv where key=?',(q['key'],)).fetchone(); con.close()
                    f.write((json.dumps({'value':v,'revision':r},sort_keys=True)+'\n').encode()); f.flush()
                f.close(); cc.close()
            threading.Thread(target=serve,args=(c,),daemon=True).start()
        s.close()
    t=threading.Thread(target=server,daemon=True); t.start(); ready.wait(2); return stop,t,rec

def start_cap_broker(sock,db):
    rec={'request':False,'sent_fd':False,'eof':False,'error':None}
    done=threading.Event()
    def run():
        try:
            msg=sock.recv(16)
            if not msg:
                rec['eof']=True; return
            rec['request']=True
            if msg.startswith(b'GET'):
                fd=os.open(db,os.O_RDONLY)
                sock.sendmsg([b'F'],[(socket.SOL_SOCKET,socket.SCM_RIGHTS,array.array('i',[fd]))])
                os.close(fd); rec['sent_fd']=True
        except Exception as e:
            rec['error']=type(e).__name__+':'+str(e)
        finally:
            try: sock.close()
            except OSError: pass
            done.set()
    t=threading.Thread(target=run,daemon=True); t.start(); return t,done,rec

def commit_with_token(db,token):
    con=sqlite3.connect(db,isolation_level=None); con.execute('begin immediate'); mm=[]
    for k,exp in sorted(token.items()):
        actual=con.execute('select revision from kv where key=?',(k,)).fetchone()[0]
        if actual!=exp: mm.append({'key':k,'expected':exp,'actual':actual})
    if mm:
        con.execute('rollback'); committed=False
    else:
        con.execute('update coordination set generation=2'); con.execute("insert into events values('generation_commit',2)"); con.execute('commit'); committed=True
    con.close(); return committed,mm

def snapshot(db):
    con=sqlite3.connect(db); kv={k:{'value':v,'revision':r} for k,v,r in con.execute('select key,value,revision from kv order by key')}
    g=con.execute('select generation from coordination').fetchone()[0]; ev=[list(x) for x in con.execute('select kind,generation from events order by rowid')]; con.close()
    return {'kv':kv,'generation':g,'events':ev}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--arm',choices=['persistent_cap','cloexec_cap'],required=True); ap.add_argument('--scenario',choices=['stable','B_change'],required=True); ap.add_argument('--case-id',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=False); os.chmod(out,0o755); private=out/'private'; public=out/'public'; private.mkdir(); public.mkdir(); os.chmod(private,0o700); os.chmod(public,0o777)
    db=private/'state.db'; owner=public/'owner.sock'; con=sqlite3.connect(db); con.executescript(SCHEMA); con.commit(); con.close(); os.chmod(db,0o600)
    owner_stop,owner_thr,owner_rec=start_owner(owner,db)
    parent_cap,child_cap=socket.socketpair()
    child_fd=child_cap.fileno(); cap_thr,cap_done,cap_rec=start_cap_broker(parent_cap,db)
    here=pathlib.Path(__file__).parent; helper=here/'helper_exec.py'; task=here/'task_client.py'
    cmd=['setpriv','--reuid=65534','--regid=65534','--clear-groups','python3',str(helper),a.arm,str(child_fd),str(task),str(owner),str(db)]
    p=subprocess.Popen(cmd,pass_fds=(child_fd,),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    helper_pid=p.pid
    child_cap.close()
    stdout,stderr=p.communicate(timeout=10)
    if p.returncode: raise RuntimeError(f'child rc={p.returncode}: {stderr}')
    tr=json.loads(stdout)
    cap_done.wait(2)
    if a.scenario=='B_change':
        con=sqlite3.connect(db); con.execute("update kv set value='b2',revision=2 where key='B'"); con.commit(); con.close()
    committed,mm=commit_with_token(db,tr['token']); final=snapshot(db); st=os.stat(db); pst=os.stat(private)
    result={'case_id':a.case_id,'arm':a.arm,'scenario':a.scenario,'spawn_pid':helper_pid,'task':tr,'cap_broker':cap_rec,'owner':owner_rec,'committed':committed,'mismatches':mm,'final':final,'db_mode':oct(st.st_mode&0o777),'db_uid':st.st_uid,'private_mode':oct(pst.st_mode&0o777),'private_uid':pst.st_uid,'child_rc':p.returncode,'child_stderr':stderr}
    (out/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    owner_stop.set(); owner_thr.join(1); cap_thr.join(1)
    if owner.exists(): owner.unlink()
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
