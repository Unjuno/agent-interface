import argparse,array,importlib.util,json,os,pathlib,socket,sqlite3,subprocess,threading,struct,time
BASE = pathlib.Path(__file__).parents[1]/'scm_peercred_gate_v1'/'run_case.py'
spec=importlib.util.spec_from_file_location('peercred_base',BASE); base=importlib.util.module_from_spec(spec); spec.loader.exec_module(base)

def start_broker(sock_path, db_path, arm):
    helper=subprocess.Popen(['setpriv','--reuid=65534','--regid=65534','--clear-groups','python3','-c','import time; time.sleep(30)']); time.sleep(0.05)
    ready=threading.Event(); stop=threading.Event(); record={'connections':0,'sent_fd':False,'helper_pid':helper.pid}
    def server():
        if sock_path.exists(): sock_path.unlink()
        s=socket.socket(socket.AF_UNIX); s.bind(str(sock_path)); os.chmod(sock_path,0o666); s.listen(); s.settimeout(0.1); ready.set()
        while not stop.is_set():
            try: c,_=s.accept()
            except TimeoutError: continue
            record['connections']+=1
            peer_pid,peer_uid,peer_gid=struct.unpack('3i',c.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,struct.calcsize('3i')))
            record.update(peer_pid=peer_pid,peer_uid=peer_uid,peer_gid=peer_gid,helper_alive=helper.poll() is None)
            allow = peer_uid==65534 if arm=='uid_only' else (peer_uid==65534 and peer_pid==helper.pid)
            record['allowed']=allow; _=c.recv(16)
            if allow:
                fd=os.open(db_path,os.O_RDONLY); c.sendmsg([b'F'],[(socket.SOL_SOCKET,socket.SCM_RIGHTS,array.array('i',[fd]))]); os.close(fd); record['sent_fd']=True
            else: c.sendmsg([b'D'])
            c.close()
        s.close(); helper.terminate(); helper.wait(timeout=2)
    t=threading.Thread(target=server,daemon=True); t.start(); ready.wait(2); return stop,t,record

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--arm',choices=['uid_only','uid_pid'],required=True); ap.add_argument('--scenario',choices=['stable','B_change'],required=True); ap.add_argument('--case-id',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=False); os.chmod(out,0o755); private=out/'private'; public=out/'public'; private.mkdir(); public.mkdir(); os.chmod(private,0o700); os.chmod(public,0o777)
    db=private/'state.db'; owner=public/'owner.sock'; broker_sock=public/'broker.sock'; con=sqlite3.connect(db); con.executescript(base.SCHEMA); con.commit(); con.close(); os.chmod(db,0o600)
    os_stop,os_thr=base.start_owner(owner,db); br_stop,br_thr,broker=start_broker(broker_sock,db,a.arm)
    task=pathlib.Path(__file__).with_name('task_client.py'); p=subprocess.run(['setpriv','--reuid=65534','--regid=65534','--clear-groups','python3',str(task),str(owner),str(broker_sock),str(db)],capture_output=True,text=True,timeout=10)
    if p.returncode: raise RuntimeError(p.stderr)
    tr=json.loads(p.stdout)
    if a.scenario=='B_change':
        con=sqlite3.connect(db); con.execute("update kv set value='b2',revision=2 where key='B'"); con.commit(); con.close()
    committed,mm=base.commit_with_token(db,tr['token']); final=base.snapshot(db); st=os.stat(db); pst=os.stat(private)
    result={'case_id':a.case_id,'arm':a.arm,'scenario':a.scenario,'task':tr,'broker':broker,'committed':committed,'mismatches':mm,'final':final,'db_mode':oct(st.st_mode&0o777),'db_uid':st.st_uid,'private_mode':oct(pst.st_mode&0o777),'private_uid':pst.st_uid,'task_returncode':p.returncode,'task_stderr':p.stderr}
    (out/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n'); os_stop.set(); br_stop.set(); os_thr.join(1); br_thr.join(2)
    for q in [owner,broker_sock]:
        if q.exists(): q.unlink()
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
