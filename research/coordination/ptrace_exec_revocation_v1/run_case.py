import argparse,array,json,os,pathlib,socket,sqlite3,subprocess,threading
SCHEMA="""create table kv(key text primary key,value text not null,revision integer not null);create table coordination(generation integer not null);create table events(kind text not null,generation integer not null);insert into kv values('A','a1',1),('B','b1',1);insert into coordination values(1);"""
def start_owner(path,db):
    stop=threading.Event();ready=threading.Event();reads=[]
    def run():
        if path.exists():path.unlink()
        s=socket.socket(socket.AF_UNIX);s.bind(str(path));os.chmod(path,0o666);s.listen();s.settimeout(.1);ready.set()
        while not stop.is_set():
            try:c,_=s.accept()
            except TimeoutError:continue
            def h(cc):
                f=cc.makefile('rwb')
                for line in f:
                    q=json.loads(line);reads.append(q['key']);con=sqlite3.connect(db);v,r=con.execute('select value,revision from kv where key=?',(q['key'],)).fetchone();con.close();f.write((json.dumps({'value':v,'revision':r})+'\n').encode());f.flush()
                f.close();cc.close()
            threading.Thread(target=h,args=(c,),daemon=True).start()
        s.close()
    t=threading.Thread(target=run,daemon=True);t.start();ready.wait(2);return stop,t,reads
def start_broker(sock,db):
    rec={'request':False,'sent_fd':False,'error':None};done=threading.Event()
    def run():
        try:
            msg=sock.recv(16);rec['request']=bool(msg)
            if msg.startswith(b'GET'):
                fd=os.open(db,os.O_RDONLY);sock.sendmsg([b'F'],[(socket.SOL_SOCKET,socket.SCM_RIGHTS,array.array('i',[fd]))]);os.close(fd);rec['sent_fd']=True
        except Exception as e:rec['error']=type(e).__name__+':'+str(e)
        finally:
            try:sock.close()
            except OSError:pass
            done.set()
    t=threading.Thread(target=run,daemon=True);t.start();return t,done,rec
def commit(db,token):
    c=sqlite3.connect(db,isolation_level=None);c.execute('begin immediate');mm=[]
    for k,e in sorted(token.items()):
        ac=c.execute('select revision from kv where key=?',(k,)).fetchone()[0]
        if ac!=e:mm.append({'key':k,'expected':e,'actual':ac})
    if mm:c.execute('rollback');ok=False
    else:c.execute('update coordination set generation=2');c.execute("insert into events values('generation_commit',2)");c.execute('commit');ok=True
    c.close();return ok,mm
def snap(db):
    c=sqlite3.connect(db);kv={k:{'value':v,'revision':r} for k,v,r in c.execute('select key,value,revision from kv')};g=c.execute('select generation from coordination').fetchone()[0];ev=[list(x) for x in c.execute('select kind,generation from events')];c.close();return {'kv':kv,'generation':g,'events':ev}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--arm',choices=['no_observer','ptrace_exec_revoke'],required=True);ap.add_argument('--scenario',choices=['stable','B_change'],required=True);ap.add_argument('--case-id',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();out=pathlib.Path(a.out);out.mkdir(parents=True);os.chmod(out,0o755);pr=out/'private';pu=out/'public';pr.mkdir();pu.mkdir();os.chmod(pr,0o700);os.chmod(pu,0o777);db=pr/'state.db';owner=pu/'owner.sock';c=sqlite3.connect(db);c.executescript(SCHEMA);c.commit();c.close();os.chmod(db,0o600)
    st,th,reads=start_owner(owner,db);p_cap,c_cap=socket.socketpair();p_ctrl,c_ctrl=socket.socketpair();here=pathlib.Path(__file__).parent
    broker_thr=broker_done=broker_rec=None
    if a.arm=='no_observer':broker_thr,broker_done,broker_rec=start_broker(p_cap,db)
    cmd=['setpriv','--reuid=65534','--regid=65534','--clear-groups','python3',str(here/'supervisor.py'),'--arm',a.arm,'--cap-fd',str(c_cap.fileno()),'--ctrl-fd',str(c_ctrl.fileno()),'--helper',str(here/'helper_exec.py'),'--task',str(here/'task_client.py'),'--owner',str(owner),'--db',str(db)]
    p=subprocess.Popen(cmd,pass_fds=(c_cap.fileno(),c_ctrl.fileno()),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);c_cap.close();c_ctrl.close()
    revoked=False
    if a.arm=='ptrace_exec_revoke':
        msg=p_ctrl.recv(16)
        if msg!=b'EXEC\n':raise RuntimeError(f'bad exec notice {msg}')
        p_cap.close();revoked=True;p_ctrl.sendall(b'ACK\n')
    p_ctrl.close();stdout,stderr=p.communicate(timeout=10)
    if p.returncode:raise RuntimeError(stderr)
    sup=json.loads(stdout)
    if a.arm=='no_observer':broker_done.wait(2);broker_thr.join(1)
    if a.scenario=='B_change':c=sqlite3.connect(db);c.execute("update kv set value='b2',revision=2 where key='B'");c.commit();c.close()
    ok,mm=commit(db,sup['task']['token']);final=snap(db)
    r={'case_id':a.case_id,'arm':a.arm,'scenario':a.scenario,'supervisor':sup,'grantor_revoked_on_exec':revoked,'broker':broker_rec,'owner_reads':reads,'committed':ok,'mismatches':mm,'final':final};(out/'result.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n');st.set();th.join(1);print(json.dumps(r,sort_keys=True))
if __name__=='__main__':main()
