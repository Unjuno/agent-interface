"""Scripted visual correction and stalled reply tests through the shared executor."""
import argparse,hashlib,json,shutil,threading,time
from pathlib import Path
from session_v14 import Backend,suite
from executor_v3 import Executor
HERE=Path(__file__).resolve().parent
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    names=['session_v14.py','session_v13.py','session_v12.py','session_v11.py','session_v9.py','session_v8.py','session_v7.py','session_v6.py','session_v5.py','session_v4.py','input_owner_v8.py','pointer_reply.py','executor_v3.py','lease.py']
    paths=[HERE/n for n in names]+[Path(__file__).resolve()]
    (a.out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2)+'\n')
    s=suite.Session();backend=None;engine=None;events=[];rows=[];blocked=threading.Event();resume=threading.Event();last_offer=None;target=None;output=None
    def emit(r):
        nonlocal last_offer
        r['emitted_ns']=time.perf_counter_ns();events.append(r)
        if r['event']=='pointer_yield':
            last_offer=r
            if r['id']=='visual':
                box=suite.red_bbox(backend.decoder.frame);state=backend.owner.call('input_state');dx=target-box[0]
                command={'op':'finish'} if abs(dx)<=1 else {'op':'move','x':state['pointer'][0]+dx,'y':state['pointer'][1]}
                try:backend.reply_pointer(r['ticket'],r['sequence']-1,command)
                except ValueError:pass
                else:raise AssertionError('stale sequence accepted')
                backend.reply_pointer(r['ticket'],r['sequence'],command)
                try:backend.reply_pointer(r['ticket'],r['sequence'],command)
                except ValueError:pass
                else:raise AssertionError('duplicate accepted')
                rows.append({'case':'visual_reply','bbox':box,'command':command})
            else:blocked.set();assert resume.wait(3)
    def submit(name,steps,ms=5000):engine.submit(name,steps,backend.sequence,time.perf_counter_ns()+ms*1_000_000)
    def wait():
        end=time.monotonic()+6
        while engine.active is not None and time.monotonic()<end:time.sleep(.01)
        assert engine.active is None
        return next(r for r in reversed(events) if r['event']=='terminal')
    try:
        goal,output,_=suite.prepare(s,'inkscape',991003,'unused');backend=Backend(s,a.out,emit);engine=Executor(backend,emit);backend.snapshot('initial',0)
        box=suite.red_bbox(backend.decoder.frame);target=box[0]+24;x=(box[0]+box[2])//2;y=(box[1]+box[3])//2
        guide={'op':'pointer_guided','points':[{'x':x,'y':y},{'x':x+12,'y':y}],'duration_ms':100,'reply_timeout_ms':1000,'max_updates':2,'feedback_delay_ms':80}
        submit('visual',[guide]);assert wait()['status']=='completed'
        submit('save',[{'op':'chord','modifier':'Control_L','key':'s'},{'op':'settle','quiet_ms':100,'timeout_ms':1200}]);assert wait()['status']=='completed'
        after=suite.red_bbox(backend.decoder.frame);evaluation=suite.evaluate('inkscape',output,goal)
        rows.append({'case':'visual_result','requested_dx':24,'observed_dx':after[0]-box[0],'within_one_pixel':abs(after[0]-target)<=1,'evaluation':evaluation})
        assert evaluation['success'] and abs(after[0]-target)<=1
        for name,ms in [('reply_timeout',4000),('original_expiry',500)]:
            backend.snapshot(name+'-fresh',0);blocked.clear();resume.clear()
            submit(name,[dict(guide,points=[{'x':400,'y':250},{'x':410,'y':250}],max_updates=1)],ms)
            assert blocked.wait(2);end=time.monotonic()+2
            while time.monotonic()<end:
                state=backend.owner.call('input_state')
                if not state['owned_buttons']:break
                time.sleep(.005)
            assert not state['owned_buttons'] and engine.active is not None
            try:backend.reply_pointer(last_offer['ticket'],last_offer['sequence'],{'op':'move','x':420,'y':250})
            except ValueError:pass
            else:raise AssertionError('late reply accepted')
            resume.set();terminal=wait();assert terminal['status']==('needs_decision' if name=='reply_timeout' else 'expired') and terminal['release']['verified'],terminal
            assert backend.owner.call('input_state')['pointer']==[410,250]
            rows.append({'case':name,'released_while_delivery_blocked':True,'terminal':terminal['status'],'no_late_motion':True})
    except Exception as e:rows.append({'error':repr(e)});raise
    finally:
        resume.set()
        if engine:engine.close()
        if backend:backend.close();(a.out/'owner-events.json').write_text(json.dumps(backend.owner.records,indent=2)+'\n')
        if output and output.exists():shutil.copy2(output,a.out/'shape.svg')
        (a.out/'events.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in events));(a.out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
        s.close();(a.out/'cleanup.json').write_text(json.dumps({'all_owned_processes_exited':all(p.poll() is not None for p in s.procs)})+'\n');shutil.rmtree(s.tmp)
    print(json.dumps(rows))
if __name__=='__main__':main()
