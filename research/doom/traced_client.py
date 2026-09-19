"""Transparent local pipe client; record receipt, do not select/renew actions."""
import argparse,hashlib,json,subprocess,sys,threading,time
from pathlib import Path

HERE=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--seed',type=int,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    manifest=dict(seed=a.seed,entrypoint='session_v7.py',presentation='full',
        clock='client and child time.perf_counter_ns in same WSL instance',
        scope='local pipe receipt is not tool return or model receipt',
        sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'session_v7.py')})
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    lock=threading.Lock();errors=[]
    def trace(event,**fields):
        row=dict(event=event,client_ns=time.perf_counter_ns(),**fields)
        with lock:
            with (a.out/'client.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
    with (a.out/'runtime-stderr.txt').open('w') as err:
        p=subprocess.Popen([sys.executable,str(HERE/'session_v7.py'),'--seed',str(a.seed),
            '--out',str(a.out/'runtime')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1)
        def reader():
            latest=None
            try:
                for line in p.stdout:
                    received=time.perf_counter_ns();row=json.loads(line)
                    trace('runtime_received',received_ns=received,record=row)
                    if row['event']=='observation':latest=row
                    if latest is not None:
                        data=dict(observation=latest,last_event=row['event'])
                        if row['event']=='terminal':data['terminal']=row
                        temp=a.out/'feedback.tmp';temp.write_text(json.dumps(data));temp.replace(a.out/'feedback.json')
                    print(line,end='',flush=True)
                    trace('stdout_write_returned',runtime_event=row['event'],runtime_emit_ns=row['emit_ns'])
            except Exception as exc:
                errors.append(repr(exc));trace('reader_error',error=repr(exc))
        t=threading.Thread(target=reader);t.start()
        try:
            for line in sys.stdin:
                command=json.loads(line)
                trace('command_received',command=command)
                p.stdin.write(line);p.stdin.flush()
                trace('command_write_returned',command_id=command.get('id'),operation=command['op'])
                if command['op']=='finish':break
        finally:
            p.stdin.close()
            try:p.wait(timeout=20)
            except subprocess.TimeoutExpired:
                trace('shutdown_timeout');p.terminate();p.wait(timeout=5)
            t.join(timeout=5)
            trace('client_closed',child_returncode=p.returncode,reader_alive=t.is_alive(),errors=errors)
        if p.returncode or errors or t.is_alive():raise SystemExit(1)

if __name__=='__main__':main()
