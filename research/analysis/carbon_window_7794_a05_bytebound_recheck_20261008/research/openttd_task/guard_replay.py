"""Scripted replay of published visual action coordinates, not a new agent episode."""
import argparse,hashlib,json,queue,signal,subprocess,sys,threading,time
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--root',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    steps=[
        [{'op':'pointer_click','x':820,'y':51}],
        [{'op':'pointer_click','x':709,'y':90},{'op':'pointer_move','x':673,'y':381}],
        [{'op':'pointer_drag','points':[{'x':685,'y':383},{'x':641,'y':405},{'x':597,'y':427}],'duration_ms':300},{'op':'observe'}]]
    (a.out/'replay-plan.json').write_text(json.dumps({'scope':'scripted prior-coordinate replay; no assistant success claim','programs':steps,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n')
    with (a.out/'runner-stderr.txt').open('w') as err,(a.out/'runner-stdout.txt').open('w') as transcript:
        p=subprocess.Popen([sys.executable,str(HERE/'interactive_v2.py'),'--out',str(a.out/'episode'),'--root',str(a.root),'--controller','scripted'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True)
        q=queue.Queue()
        def reader():
            for line in p.stdout:
                transcript.write(line);transcript.flush()
                try:q.put(json.loads(line))
                except ValueError:pass
            q.put(None)
        t=threading.Thread(target=reader,daemon=True);t.start();sequence=0
        def wait(event):
            nonlocal sequence
            end=time.monotonic()+45
            while time.monotonic()<end:
                r=q.get(timeout=max(.1,end-time.monotonic()))
                if r is None:raise RuntimeError('adapter exited')
                if r['event']=='observation':sequence=r['sequence']
                if r['event']=='rejected':raise RuntimeError(r)
                if r['event']==event:return r
            raise TimeoutError(event)
        def send(c):p.stdin.write(json.dumps(c)+'\n');p.stdin.flush()
        try:
            wait('observation')
            for i,program in enumerate(steps):
                send({'op':'submit','id':f'replay-{i}','expected_sequence':sequence,'valid_until_ns':time.perf_counter_ns()+5_000_000_000,'steps':program})
                r=wait('terminal');assert r['status']=='completed' and r['release']['verified'],r
            send({'op':'finish'});result=wait('independent_evaluation');print(json.dumps(result),flush=True)
            p.stdin.close();assert p.wait(timeout=10)==0
        finally:
            if p.poll() is None:
                p.send_signal(signal.SIGINT)
                p.wait(timeout=10)
            t.join(timeout=2)

if __name__=='__main__':main()
