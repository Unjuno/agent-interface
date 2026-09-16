import argparse, json, os, pathlib, socket, sqlite3, subprocess, threading

SCHEMA = '''
create table kv(key text primary key, value text not null, revision integer not null);
create table coordination(generation integer not null);
create table events(kind text not null, generation integer not null);
insert into kv values('A','a1',1),('B','b1',1);
insert into coordination values(1);
'''

def handle_client(conn_sock, db_path):
    f = conn_sock.makefile('rwb')
    for line in f:
        req = json.loads(line)
        con = sqlite3.connect(db_path, isolation_level=None)
        if req['op'] == 'read':
            value, revision = con.execute('select value,revision from kv where key=?',(req['key'],)).fetchone()
            out = {'value': value, 'revision': revision}
        else:
            out = {'error':'unsupported'}
        con.close()
        f.write((json.dumps(out, sort_keys=True)+'\n').encode()); f.flush()
    f.close(); conn_sock.close()

def start_server(sock_path, db_path):
    ready = threading.Event(); stop = threading.Event()
    def server():
        if sock_path.exists(): sock_path.unlink()
        s = socket.socket(socket.AF_UNIX)
        s.bind(str(sock_path)); os.chmod(sock_path,0o666); s.listen(); s.settimeout(0.1); ready.set()
        while not stop.is_set():
            try: c,_ = s.accept()
            except TimeoutError: continue
            threading.Thread(target=handle_client,args=(c,db_path),daemon=True).start()
        s.close()
    t=threading.Thread(target=server,daemon=True); t.start(); ready.wait(2)
    return stop,t

def commit_with_token(db_path, token):
    con = sqlite3.connect(db_path, isolation_level=None)
    con.execute('begin immediate')
    mismatches=[]
    for key, expected in sorted(token.items()):
        actual=con.execute('select revision from kv where key=?',(key,)).fetchone()[0]
        if actual != expected: mismatches.append({'key':key,'expected':expected,'actual':actual})
    if mismatches:
        con.execute('rollback'); committed=False
    else:
        con.execute('update coordination set generation=2')
        con.execute("insert into events values('generation_commit',2)")
        con.execute('commit'); committed=True
    con.close(); return committed,mismatches

def snapshot(db_path):
    con=sqlite3.connect(db_path)
    rows={k:{'value':v,'revision':r} for k,v,r in con.execute('select key,value,revision from kv order by key')}
    generation=con.execute('select generation from coordination').fetchone()[0]
    events=con.execute('select kind,generation from events order by rowid').fetchall()
    con.close(); return {'kv':rows,'generation':generation,'events':[list(x) for x in events]}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--arm',choices=['unrestricted','mediated'],required=True); ap.add_argument('--scenario',choices=['stable','B_change'],required=True); ap.add_argument('--case-id',required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
    out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=False)
    private=out/'private'; public=out/'public'; private.mkdir(); public.mkdir(); os.chmod(out,0o755); os.chmod(private,0o700); os.chmod(public,0o777)
    db=private/'state.db'; sock=public/'owner.sock'
    con=sqlite3.connect(db); con.executescript(SCHEMA); con.commit(); con.close(); os.chmod(db,0o600)
    stop,thread=start_server(sock,db)
    task_script=pathlib.Path(__file__).with_name('task_client.py')
    cmd=['python3',str(task_script),str(sock),str(db)]
    if args.arm=='mediated':
        cmd=['setpriv','--reuid=65534','--regid=65534','--clear-groups']+cmd
    proc=subprocess.run(cmd,capture_output=True,text=True,check=False,timeout=10)
    if proc.returncode != 0:
        raise RuntimeError(f'task failed rc={proc.returncode} stderr={proc.stderr}')
    task=json.loads(proc.stdout)
    if args.scenario=='B_change':
        con=sqlite3.connect(db); con.execute("update kv set value='b2', revision=2 where key='B'"); con.commit(); con.close()
    committed,mismatches=commit_with_token(db,task['token'])
    final=snapshot(db)
    stat=os.stat(db)
    result={
      'case_id':args.case_id,'arm':args.arm,'scenario':args.scenario,'task':task,
      'committed':committed,'mismatches':mismatches,'final':final,
      'db_mode':oct(stat.st_mode & 0o777),'db_uid':stat.st_uid,'private_mode':oct(os.stat(private).st_mode & 0o777),'private_uid':os.stat(private).st_uid,
      'task_returncode':proc.returncode,'task_stderr':proc.stderr,
    }
    (out/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    stop.set(); thread.join(1)
    if sock.exists(): sock.unlink()
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
