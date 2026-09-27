"""Real Inkscape integration pilot, scripted planner and independent saved scoring."""
import hashlib,json,shutil,time,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from session_v15 import Backend,suite
from executor_v3 import Executor
from patch_servo import PatchServo
HERE=Path(__file__).resolve().parent
root=HERE/'results/patch-servo-03';root.mkdir(exist_ok=False)
allrows=[]
for offset in (0,40):
    out=root/str(offset);out.mkdir();s=suite.Session();backend=None;engine=None;output=None;servo=None;events=[]
    def image():
        f=backend.decoder.frame
        return np.frombuffer(f.pixels,dtype=np.uint8).reshape(f.height,f.width,3)
    def emit(r):
        r['emitted_ns']=time.perf_counter_ns();events.append(r)
        if r['event']=='pointer_yield':
            state=backend.owner.call('input_state')
            command=servo.reply(image(),r['sequence'],str(backend.observed_pointer),state['pointer'])
            backend.reply_pointer(r['ticket'],r['sequence'],command)
    def run(name,steps):
        engine.submit(name,steps,backend.sequence,time.perf_counter_ns()+8_000_000_000)
        end=time.monotonic()+10
        while engine.active is not None and time.monotonic()<end:time.sleep(.01)
        assert engine.active is None
        return next(r for r in reversed(events) if r['event']=='terminal')
    def rect():
        r=ET.parse(output).getroot().find('{http://www.w3.org/2000/svg}rect')
        return {k:r.get(k) for k in ('x','y','width','height','transform')}
    save=[{'op':'chord','modifier':'Control_L','key':'s'},{'op':'settle','quiet_ms':100,'timeout_ms':1200}]
    try:
        goal,output,_=suite.prepare(s,'inkscape',991007+offset,'unused');backend=Backend(s,out,emit);engine=Executor(backend,emit);backend.snapshot('initial',0)
        if offset:
            b=suite.red_bbox(backend.decoder.frame);x=(b[0]+b[2])//2;y=(b[1]+b[3])//2
            assert run('setup_offset',[{'op':'pointer_drag','points':[{'x':x+2*i,'y':y} for i in range(offset//2+1)],'duration_ms':200}]+save)['status']=='completed'
        if offset:assert abs(float(rect()['x'])-50)>5, 'setup displacement failed'
        assert run('deselect',[{'op':'key','key':'Escape'},{'op':'settle','quiet_ms':100,'timeout_ms':1200}])['status']=='completed'
        before=rect();backend.snapshot('source',0)
        # Fixture-specific planner setup only; the correction policy never calls red_bbox.
        b=suite.red_bbox(backend.decoder.frame);x=(b[0]+b[2])//2;y=(b[1]+b[3])//2
        box=[b[0]-4,b[1]-4,b[2]-b[0]+9,b[3]-b[1]+9]
        servo=PatchServo(image(),box,backend.sequence,str(backend.observed_pointer),[24,0],max_updates=3)
        start=time.perf_counter_ns()
        terminal=run('servo',[{'op':'pointer_guided','points':[{'x':x,'y':y},{'x':x+12,'y':y}],'duration_ms':100,'reply_timeout_ms':1000,'max_updates':4,'feedback_delay_ms':80}])
        duration=(time.perf_counter_ns()-start)/1e6
        assert run('save',save)['status']=='completed'
        after=rect();dx=(float(after['x'])-float(before['x']))*1.18
        preserved=all(after[k]==before[k] for k in ('y','width','height','transform'))
        row={'setup_offset_requested':offset,'source_box':box,'before':before,'after':after,'saved_dx_screen':dx,'preserved':preserved,'precision_pass':abs(dx-24)<=1,'terminal':terminal,'controller':servo.records,'program_ms':duration}
        allrows.append(row)
        (out/'result.json').write_text(json.dumps(row,indent=2)+'\n')
    finally:
        if engine:engine.close()
        if backend:
            backend.close();(out/'owner-events.json').write_text(json.dumps(backend.owner.records,indent=2)+'\n')
        (out/'events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
        if output and output.exists():shutil.copy2(output,out/'shape.svg')
        s.close();shutil.rmtree(s.tmp)
sources=[Path(__file__),HERE/'patch_servo.py',HERE/'visual_anchor.py',HERE/'session_v15.py',HERE/'input_owner_v9.py',HERE/'pointer_reply_v2.py',HERE/'executor_v3.py']
(root/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2)+'\n')
print(json.dumps(allrows,indent=2))
