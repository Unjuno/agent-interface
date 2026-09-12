"""Interactive async X11 research session; normal stdin remains a control lane.

No network service or arbitrary code evaluation. All GUI access has one worker
owner. Accept/cancel messages are emitted by the reader while that worker runs.
"""
import argparse
import contextlib
import hashlib
import json
import math
import shutil
import sys
import threading
import time
from pathlib import Path
from PIL import ImageGrab

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Encoder,Decoder,Frame
from image_artifact import ImageArtifactSink
import gui_suite as suite
from executor_v3 import Executor,Cancelled,DecisionRequired
from lease import Expired

TEXT='abcdefghijklmnopqrstuvwxyz0123456789:/-._ '
KEYS=set(TEXT[:36])|{'Return','Tab','Escape','Left','Right','Up','Down','F1','space',
                        'Control_L','Shift_L','Alt_L','semicolon','slash','minus','period'}


def number(value,low,high):
    return type(value) in (int,float) and math.isfinite(value) and low<=value<=high


class Backend:
    def __init__(self,session,out,emit):
        self.session,self.out,self.emit=session,out,emit
        self.encoder,self.decoder=Encoder('live-control','O2',64),Decoder('live-control')
        self.images=ImageArtifactSink(out,compress_level=1,reuse=True)
        self.held=set(); self.touched=set(); self.sequence=0
        self.last_context={}

    def validate(self,steps):
        if not isinstance(steps,list) or not 1<=len(steps)<=16: raise ValueError('1–16 steps required')
        budget_ms=0
        for step in steps:
            if not isinstance(step,dict): raise ValueError('step must be object')
            op=step.get('op')
            if op=='text':
                value=step.get('text')
                if not isinstance(value,str) or len(value)>128 or any(c not in TEXT for c in value):
                    raise ValueError('unsupported text; reject entire program before input')
            elif op=='key':
                if step.get('key') not in KEYS: raise ValueError('unsupported key')
            elif op=='chord':
                if step.get('modifier') not in ('Control_L','Shift_L','Alt_L') or step.get('key') not in KEYS:
                    raise ValueError('unsupported chord')
            elif op=='hold':
                keys=step.get('keys')
                if not isinstance(keys,list) or not 1<=len(keys)<=4 or len(set(keys))!=len(keys) or any(k not in KEYS for k in keys):
                    raise ValueError('1–4 unique supported keys required')
                if not number(step.get('duration_ms'),1,5000): raise ValueError('hold must be 1–5000 ms')
                budget_ms+=step['duration_ms']
            elif op=='wait_title':
                if not isinstance(step.get('contains'),str) or not step['contains'] or len(step['contains'])>128:
                    raise ValueError('nonempty title condition required')
                if not number(step.get('timeout_ms'),1,5000): raise ValueError('timeout must be 1–5000 ms')
                budget_ms+=step['timeout_ms']
            elif op not in ('observe','decide'): raise ValueError('unsupported operation')
        if budget_ms>10000: raise ValueError('combined hold/wait budget exceeds 10 seconds')

    def raw(self,key,down):
        if down:
            self.lease.check()
            self.emit(dict(event='input_admission',key=key,admitted_ns=time.perf_counter_ns(),valid_until_ns=self.lease.deadline))
        code=self.session.d.keysym_to_keycode(suite.base.XK.string_to_keysym(key))
        if not code: raise ValueError('key unavailable on this backend')
        self.touched.add(key)
        if down:self.held.add(key)
        suite.base.xtest.fake_input(self.session.d,suite.base.X.KeyPress if down else suite.base.X.KeyRelease,code)
        self.session.d.sync()
        if not down:self.held.discard(key)

    def release_all(self):
        for key in list(self.held): self.raw(key,False)
        bitmap=self.session.d.query_keymap()
        still_down=[]
        for key in self.touched:
            code=self.session.d.keysym_to_keycode(suite.base.XK.string_to_keysym(key))
            if bitmap[code//8] & (1 << (code%8)):still_down.append(key)
        self.touched.clear()
        if still_down: raise RuntimeError('X11 still reports keys down: '+repr(still_down))
        return dict(verified=True,keys_down=still_down,verified_ns=time.perf_counter_ns())

    def snapshot(self,identifier,index):
        start=time.perf_counter_ns()
        im=ImageGrab.grab(xdisplay=self.session.name).convert('RGB')
        capture=time.perf_counter_ns()
        source=Frame(im.width,im.height,im.mode,im.tobytes())
        context=self.session.context(); context_ns=time.perf_counter_ns()
        packet=self.encoder.encode(source,action_id=f'{identifier}:{index}',observed_ns=capture,context=context)
        frame=self.decoder.accept(packet)
        if frame!=source:raise AssertionError('wire reconstruction failed')
        self.sequence+=1
        (self.out/f'{self.sequence:03d}.ait').write_bytes(packet)
        artifact=self.images.publish(frame)
        self.last_context=dict(context)
        self.emit(dict(event='observation',id=identifier,step=index,sequence=self.sequence,
                       capture_ns=capture,context_ns=context_ns,context=context,**artifact,
                       capture_ms=(capture-start)/1e6,wire_bytes=len(packet),exact=True,
                       semantic_completion='unknown'))

    def execute(self,step,cancel,identifier,index):
        def checkpoint():
            if cancel.is_set():raise Cancelled()
        def press(key): self.raw(key,True); self.raw(key,False)
        checkpoint(); op=step['op']
        if op=='text':
            mapping={':':('semicolon',True),'/':('slash',False),'-':('minus',False),
                     '.':('period',False),'_':('minus',True),' ':('space',False)}
            for i,ch in enumerate(step['text']):
                checkpoint()
                key,shift=mapping.get(ch,(ch,False))
                if shift:self.raw('Shift_L',True)
                press(key)
                if shift:self.raw('Shift_L',False)
                if i+1<len(step['text']) and cancel.wait(.002):raise Cancelled()
        elif op=='key':press(step['key'])
        elif op=='chord':
            self.raw(step['modifier'],True)
            try:press(step['key'])
            finally:self.raw(step['modifier'],False)
        elif op=='hold':
            try:
                for key in step['keys']:checkpoint(); self.raw(key,True)
                self.emit(dict(event='keys_held',id=identifier,step=index,keys=sorted(self.held),
                               input_ack_ns=time.perf_counter_ns()))
                deadline=time.perf_counter()+step['duration_ms']/1000
                while time.perf_counter()<deadline:
                    checkpoint(); self.snapshot(identifier,index)
                    if cancel.wait(min(.05,max(0,deadline-time.perf_counter()))):raise Cancelled()
            finally:
                for key in list(self.held):self.raw(key,False)
        elif op=='wait_title':
            deadline=time.perf_counter()+step['timeout_ms']/1000
            while True:
                checkpoint(); self.snapshot(identifier,index)
                if step['contains'] in self.last_context['windows']:
                    self.emit(dict(event='condition_met',id=identifier,step=index,
                                   condition=step,known_ns=time.perf_counter_ns(),evidence='public X11 window title'))
                    return
                if time.perf_counter()>=deadline:raise TimeoutError('public title condition')
                if cancel.wait(.016):raise Cancelled()
        checkpoint()
        self.snapshot(identifier,index)
        if op=='decide':raise DecisionRequired()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--app',choices=suite.APPS,required=True)
    ap.add_argument('--seed',type=int,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--chromium',default='/home/taka/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome')
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    lock=threading.Lock();events=[]
    def emit(record):
        with lock:
            record['emit_started_ns']=time.perf_counter_ns();events.append(record)
            line=json.dumps(record)
            with (args.out/'events.jsonl').open('a') as log:log.write(line+'\n')
            try:print(line,flush=True)
            except BrokenPipeError:pass
    session=None;server=None;engine=None;output=None
    try:
        hashes={}
        for path in [HERE/'executor_v3.py',HERE/'session_v3.py',HERE/'lease.py',HERE.parent/'observation_tiles/tile_transport.py',
                     HERE.parent/'observation_tiles/image_artifact.py',HERE.parent/'observation_gating/gui_suite.py',
                     HERE.parent/'observation_gating/exact_gate.py',HERE.parent/'real_apps_v1/real_app_suite_v1.py']:
            hashes[str(path.relative_to(HERE.parent))]=hashlib.sha256(path.read_bytes()).hexdigest()
        suite.write_json(args.out/'sources.json',hashes)
        # Xlib emits setup diagnostics to stdout. Keep the control lane JSON-only.
        # This redirect ends before the executor thread starts.
        with (args.out/'setup-diagnostics.txt').open('w') as diagnostics, contextlib.redirect_stdout(diagnostics):
            session=suite.Session();goal,output,server=suite.prepare(session,args.app,args.seed,args.chromium)
        backend=Backend(session,args.out,emit);engine=Executor(backend,emit)
        emit(dict(event='ready',app=args.app,goal=goal,operations=['submit','cancel','finish']))
        backend.snapshot('initial',0)
        for line in sys.stdin:
            try:
                command=json.loads(line);emit(dict(event='command',command=command,received_ns=time.perf_counter_ns()))
                if command['op']=='submit':engine.submit(command['id'],command['steps'],command['expected_sequence'],command['valid_until_ns'])
                elif command['op']=='cancel':engine.cancel(command['id'])
                elif command['op']=='finish':
                    engine.close()
                    emit(dict(event='independent_evaluation',**suite.evaluate(args.app,output,goal)))
                    break
                else:raise ValueError('unsupported command')
            except (ValueError,KeyError,TypeError,Expired) as exc:
                emit(dict(event='rejected',reason=str(exc)))
    finally:
        if engine is not None:engine.close()
        if output is not None and output.exists():shutil.copy2(output,args.out/output.name)
        if server is not None:server.shutdown();server.server_close()
        if session is not None:session.close();shutil.rmtree(session.tmp)


if __name__=='__main__':main()
