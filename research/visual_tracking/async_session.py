"""Bounded image-based tracking through the existing asynchronous executor."""
import argparse,contextlib,hashlib,json,shutil,sys,threading,time
from pathlib import Path
from PIL import Image

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'live_control'))
from session_v2 import Backend as BaseBackend,number,suite
from executor_v2 import Executor,Cancelled
from run import locate


class Backend(BaseBackend):
    def validate(self,steps):
        if not isinstance(steps,list):raise ValueError('program must be list')
        other=[];budget=0
        for step in steps:
            if isinstance(step,dict) and step.get('op')=='track_red':
                if not number(step.get('duration_ms'),100,30000):raise ValueError('track duration must be 100–30000 ms')
                budget+=step['duration_ms'];other.append(dict(op='observe'))
            else:other.append(step)
        if budget>30000:raise ValueError('tracking budget exceeds 30 seconds')
        super().validate(other)

    def execute(self,step,cancel,identifier,index):
        if step['op']!='track_red':return super().execute(step,cancel,identifier,index)
        deadline=time.perf_counter()+step['duration_ms']/1000
        while time.perf_counter()<deadline:
            tick=time.perf_counter()
            if cancel.is_set():raise Cancelled()
            self.snapshot(identifier,index)
            frame=self.decoder.frame
            target,player=locate(Image.frombytes(frame.mode,(frame.width,frame.height),frame.pixels))
            if cancel.is_set():raise Cancelled()
            desired='Right' if target-player>18 else 'Left' if target-player < -18 else None
            for key in list(self.held):
                if key!=desired:self.raw(key,False)
            if desired is not None and desired not in self.held:self.raw(desired,True)
            self.emit(dict(event='motor_feedback',id=identifier,step=index,sequence=self.sequence,
                           target_x=target,player_x=player,held=sorted(self.held),input_ack_ns=time.perf_counter_ns()))
            if cancel.wait(max(0,.05-(time.perf_counter()-tick))):raise Cancelled()
        # A completed method releases movement before any following step.
        self.release_all()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--seed',type=int,required=True);ap.add_argument('--seconds',type=float,default=20)
    a=ap.parse_args()
    if not number(a.seconds,1,30):raise ValueError('arena duration 1–30 seconds required')
    a.out.mkdir(parents=True,exist_ok=False);lock=threading.Lock();session=None;engine=None
    def emit(row):
        with lock:
            row['emit_ns']=time.perf_counter_ns();line=json.dumps(row)
            with (a.out/'events.jsonl').open('a') as f:f.write(line+'\n')
            print(line,flush=True)
    paths=[HERE/n for n in ('async_session.py','arena.py','run.py')]
    paths += [HERE.parent/p for p in ('live_control/session_v2.py','live_control/executor_v2.py',
        'observation_gating/gui_suite.py','observation_gating/exact_gate.py','real_apps_v1/real_app_suite_v1.py',
        'observation_tiles/tile_transport.py','observation_tiles/image_artifact.py')]
    (a.out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2))
    try:
        with (a.out/'setup.txt').open('w') as f,contextlib.redirect_stdout(f):session=suite.Session()
        atom=session.d.intern_atom('_NET_SUPPORTING_WM_CHECK')
        session._wait(lambda:session.d.screen().root.get_full_property(atom,0) is not None,4,'WM readiness')
        oracle=session.tmp/'oracle.json'
        with (a.out/'app.txt').open('w') as f:
            session.spawn(['python3',str(HERE/'arena.py'),'--seed',str(a.seed),'--seconds',str(a.seconds),'--out',str(oracle)],stdout=f,stderr=f)
            session.wait_window('AI TRACK READY');session.focus('AI TRACK READY')
            backend=Backend(session,a.out,emit);engine=Executor(backend,emit)
            emit(dict(event='ready',task='Track red with green using Left/Right',arena_seconds=a.seconds))
            backend.snapshot('initial',0)
            for line in sys.stdin:
                try:
                    c=json.loads(line);emit(dict(event='command',command=c,received_ns=time.perf_counter_ns()))
                    if c['op']=='submit':engine.submit(c['id'],c['steps'],c['expected_sequence'])
                    elif c['op']=='cancel':engine.cancel(c['id'])
                    elif c['op']=='finish':
                        engine.close()
                        # Observe public completion before reading the scoring channel.
                        try:
                            session.wait_window('AI TRACK DONE',a.seconds+2)
                            truth=json.loads(oracle.read_text());shutil.copy2(oracle,a.out/'oracle.json')
                            emit(dict(event='independent_record',frames=len(truth),duration=truth[-1]['t'],
                                      note='includes uncontrolled time after cancellation; no success threshold'))
                        except TimeoutError:emit(dict(event='independent_record',available=False))
                        break
                    else:raise ValueError('unsupported operation')
                except (ValueError,TypeError,KeyError) as exc:emit(dict(event='rejected',reason=str(exc)))
    finally:
        if engine is not None:engine.close()
        if session is not None:session.close();shutil.rmtree(session.tmp)


if __name__=='__main__':main()
